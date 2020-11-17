def PredictorToColumn(analysis_model):
    columnDict = {}

    for predictor in analysis_model['model']['predictor']:
        columnDict[predictor] = analysis_model['pairs_query']['layers'][predictor]['data_avg_column']
        
    return columnDict