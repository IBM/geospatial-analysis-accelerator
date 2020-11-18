import pandas as pd
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter

def convertPDtoR(covid_pairs_df, outcome, predictors):
    # rename the column to prevent a conflict with R
    converted_df = covid_pairs_df.rename(columns={'iso3166-2_code':'iso3166_2_code'})

    # convert Pandas Data Frame to a R Data Frame
    with localconverter(ro.default_converter + pandas2ri.converter):
        r_converted_df = ro.conversion.py2rpy(converted_df)

    ro.r(_formatDataFrame(outcome, predictors))
    r_formatDataFrame = ro.globalenv['formatDataFrame']
    return r_formatDataFrame(r_converted_df)
    
def _formatDataFrame(outcome_field, predictors):
    function_start='''
    formatDataFrame <- function(myDataFrame, outcome){
        df1 <- myDataFrame

        df1$date <- as.Date(df1$date, format="%Y-%m-%d")        
        min.date <- min(df1$date)
        df1$Time <- difftime(df1$date,min.date,units="days")
        df1$Time <- as.numeric(df1$Time)
        df1$DOW <- as.factor(weekdays(df1$date)) # factor    

        df1$Region <- as.factor(df1$iso3166_2_code)
        '''

    function_end='''
        df2 <- df1[df1$logyt!=-Inf,]
    }
    '''

    #Define GAM Outcome
    #yt = outcome at Time T
    function_outcome_field = (
        f"df1$yt<-df1${outcome_field} + 1\n"
        f"df1$logyt<-log(df1$yt)\n"
    )

    #Define GAM Predictors
    function_predictors = ""

    for predictor, column in predictors.items():
        if predictor == "TemperatureAboveGround": #THIS NEEDS TO CHANGE TO A CONFIG
            function_predictors += f"df1${predictor}<-df1${column}-273.15\n"
        else:
            function_predictors += f"df1${predictor}<-df1${column}\n"

    function = "{function_start} {function_outcome_field} {function_predictors} {function_end}".\
            format(
                function_start = function_start,
                function_outcome_field = function_outcome_field,
                function_predictors = function_predictors, 
                function_end = function_end)
    return function

def determineGam(r_covid_pairs_df, independent_variables, control_variables, time_shifts, rolling_window_type, rolling_window, signicanceLevel):
    ro.r(_gamFunction(independent_variables, control_variables, rolling_window_type, rolling_window))
    r_gamFunction = ro.globalenv['gamFunction']

    r_gam_df = r_gamFunction(r_covid_pairs_df, signicanceLevel, time_shifts)
    with localconverter(ro.default_converter + pandas2ri.converter):
        gam_df = ro.conversion.rpy2py(r_gam_df)
    
    gam_df.columns = ['iso3166-2_code', 'time_shift','predictor','p_val','dev_explained','coeff','perc_change','CI_lower','CI_upper']
    return gam_df

# This function creates the string that is used to define the function in R to run the log-linear GAM model function
# Predictors, covariants and flag (avg or single) are used to create the paratemeters the function will be run against
def _gamFunction(independent_variables, control_variables, rolling_window_type, rolling_window):
    function_start='''
    library(mgcv)
    library(dplyr)
    library(zoo)

    gamFunction <- function(countrydat, sig.level=0.05, timeShifts=list(0,1,3), screen_log=FALSE){
    gams.regions.results.neg <- gams.regions.results.pos <- list() # for storing significant results
    '''

    independent_variable_list = ""
    timeshift_list = ""
    rollingmean_list = ""
    select_list = ""
    gam_list = ""
    rolling_window_function = 'rollmean' if rolling_window_type == "mean" else 'rollsum' 

    for independent_variable in independent_variables:
        delimiter = ',' if select_list != "" else ''
        delimiter_2 = ' + ' if select_list != "" else ''

        independent_variable_list = '{independent_variable_list}{delimiter}"{independent_variable}"'.format(independent_variable_list = independent_variable_list, delimiter = delimiter, independent_variable = independent_variable)

        timeshift_list = '{timeshift_list}{delimiter}{independent_variable} = lag({independent_variable},lagvar)'.format(timeshift_list = timeshift_list, delimiter = delimiter, independent_variable = independent_variable)
        rollingmean_list = '{rollingmean_list}{delimiter}{independent_variable} = {rolling_window_function}(x = {independent_variable}, {rolling_window}, align = "right", fill = NA)'.format(rollingmean_list = rollingmean_list, delimiter = delimiter, independent_variable = independent_variable,  rolling_window_function = rolling_window_function, rolling_window = rolling_window)

        select_list = '{select_list}{delimiter}{independent_variable}'.format(select_list = select_list, delimiter = delimiter, independent_variable = independent_variable)
        gam_list = '{gam_list}{delimiter_2}{independent_variable}'.format(gam_list = gam_list, delimiter_2 = delimiter_2, independent_variable = independent_variable)
    
    for control_variable in control_variables:
        delimiter = ',' if select_list != "" else ''
        delimiter_2 = ' + ' if select_list != "" else ''

        if control_variable == "DOW":
            select_list = '{select_list}{delimiter}{control_variable}'.format(select_list = select_list, delimiter = delimiter, control_variable = control_variable)
            gam_list = '{gam_list}{delimiter_2}{control_variable}'.format(gam_list = gam_list, delimiter_2 = delimiter_2, control_variable = control_variable)
        else:
            timeshift_list = '{timeshift_list}{delimiter}{control_variable} = lag({control_variable},lagvar)'.format(timeshift_list = timeshift_list, delimiter = delimiter, control_variable = control_variable)
            rollingmean_list = '{rollingmean_list}{delimiter}{control_variable} = {rolling_window_function}(x = {control_variable}, {rolling_window}, align = "right", fill = NA)'.format(rollingmean_list = rollingmean_list, delimiter = delimiter, control_variable = control_variable, rolling_window_function = rolling_window_function, rolling_window = rolling_window)
            select_list = '{select_list}{delimiter}{control_variable}'.format(select_list = select_list, delimiter = delimiter, control_variable = control_variable)
            gam_list = '{gam_list}{delimiter_2}{control_variable}'.format(gam_list = gam_list, delimiter_2 = delimiter_2, control_variable = control_variable)


    independent_variables_declare = "independent_variables <- c({independent_variable_list})".format(independent_variable_list = independent_variable_list)
    timeshift_declare = "mutate({timeshift_list}) %>%".format(timeshift_list = timeshift_list)
    rollingmean_declare = "mutate({rollingmean_list}) %>%".format(rollingmean_list = rollingmean_list)
    select_declare = "select(logyt,{select_list},Time)".format(select_list = select_list)
    gam_declare = "b.linear <- gam(logyt ~ {gam_list} + s(Time, bs='ps'), data=datgam)".format(gam_list = gam_list)

    forloop_start = '''
    for (i in levels(countrydat$Region)){
        dat <- countrydat[countrydat$Region==i,]
        dat <- dat[rowSums(is.na(dat)) != ncol(dat), ] # remove NA rows

        for (lagvar in timeShifts){
            datgam <- dat %>%
    '''
    parameter_declare = '''
            {timeshift_declare}
            {rollingmean_declare}
            {select_declare}
            {gam_declare}
    '''.format(timeshift_declare = timeshift_declare, rollingmean_declare = rollingmean_declare, select_declare = select_declare, gam_declare = gam_declare)

    forloop_end='''
            b.linear.summary <- summary(b.linear)
            pvals.linear <- b.linear.summary$p.pv[names(b.linear.summary$p.pv) %in% independent_variables]
            independent_variables.linear.index <- names(coef(b.linear)) %in% independent_variables
            independent_variables.variables.linear <- names(b.linear.summary$p.pv)[names(b.linear.summary$p.pv) %in% independent_variables]
            sig.index <- which(pvals.linear<sig.level)
            
            if (length(sig.index)>0) {
                for (j in 1:length(sig.index)) {
                if (coef(b.linear)[independent_variables.linear.index][sig.index[j]]>0){
                    ci.pos <- (exp(confint.default(b.linear, parm = independent_variables.variables.linear[sig.index[j]]))-1)*100
                    ci.pos.list <- split(ci.pos, row(ci.pos))
                    tmp.pos <- paste(i,'linear:', 'day lag:',lagvar,'days. independent_variables:',independent_variables.variables.linear[sig.index[j]],'pval:',round(pvals.linear[sig.index[j]],3),'deviance explained %:',100*round(b.linear.summary$dev.expl,3),'coeff:',round(b.linear.summary$p.coeff[independent_variables.linear.index][sig.index[j]],4), 
                                    '1 independent_variables unit change associated with % increase in cases:',round((exp(coef(b.linear)[independent_variables.linear.index][sig.index[j]])-1)*100,2),
                                    'with 95% CI:',round(unlist(ci.pos.list)[1],2), round(unlist(ci.pos.list)[2],2), sep=' ') 
                    tmp.results.pos <- c(i,lagvar,independent_variables.variables.linear[sig.index[j]],round(pvals.linear[sig.index[j]],3),100*round(b.linear.summary$dev.expl,3),round(b.linear.summary$p.coeff[independent_variables.linear.index][sig.index[j]],4),round((exp(coef(b.linear)[independent_variables.linear.index][sig.index[j]])-1)*100,2),round(unlist(ci.pos.list)[1],2), round(unlist(ci.pos.list)[2],2))
                    gams.regions.results.pos <- append(gams.regions.results.pos,tmp.results.pos)
                    if (screen_log) {
                        cat(tmp.pos, '\n')
                    }
                } else {
                    ci.neg <- (1-exp(confint.default(b.linear, parm = independent_variables.variables.linear[sig.index[j]])))*100
                    ci.neg.list <- split(ci.neg, row(ci.neg))
                    tmp.neg <- paste(i,'linear:', 'day lag:',lagvar,'days. independent_variables:',independent_variables.variables.linear[sig.index[j]],'pval:',round(pvals.linear[sig.index[j]],3),'deviance explained %:',100*round(b.linear.summary$dev.expl,3),'coeff:',round(b.linear.summary$p.coeff[independent_variables.linear.index][sig.index[j]],4), 
                                    '1 independent_variables unit change associated with % decrease in cases:',round((1-exp(coef(b.linear)[independent_variables.linear.index][sig.index[j]]))*100,2), 
                                    'with 95% CI:',round(unlist(ci.neg.list)[2],2), round(unlist(ci.neg.list)[1],2), sep=' ') 

                    tmp.results.neg <- c(i,lagvar,independent_variables.variables.linear[sig.index[j]],round(pvals.linear[sig.index[j]],3),100*round(b.linear.summary$dev.expl,3),round(b.linear.summary$p.coeff[independent_variables.linear.index][sig.index[j]],4),
                                                    round((1-exp(coef(b.linear)[independent_variables.linear.index][sig.index[j]]))*100,2),round(unlist(ci.neg.list)[2],2), round(unlist(ci.neg.list)[1],2))
                    gams.regions.results.neg <- append(gams.regions.results.neg,tmp.results.neg)
                    if (screen_log) {
                        cat(tmp.neg, '\n')
                    }

                }
                }
            }
        }
    }
    results <- data.frame(matrix(unlist(c(gams.regions.results.neg,gams.regions.results.pos)), ncol=9, byrow=T),stringsAsFactors=FALSE)
    }
    '''

    function = "{function_start} {independent_variables_declare} {forloop_start} {parameter_declare} {forloop_end}".\
        format(
            function_start = function_start,
            independent_variables_declare = independent_variables_declare,
            forloop_start = forloop_start,
            parameter_declare = parameter_declare,
            forloop_end = forloop_end
            )
    return function