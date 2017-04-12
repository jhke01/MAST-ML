import matplotlib.pyplot as plt
import matplotlib
import data_parser
import numpy as np
import os
from sklearn.kernel_ridge import KernelRidge
from sklearn.metrics import mean_squared_error
import data_analysis.printout_tools as ptools
import portion_data.get_test_train_data as gttd
import plot_data.plot_predicted_vs_measured as plotpm

def execute(model, data, savepath, lwr_data, 
            topredict_data_csv = None, 
            standard_conditions_csv = None,
            group_field_name = None,
            label_field_name = None,
            xfield = None,
            xlabel = "X",
            ylabel = "Prediction",
            overall_xlabel = "Measured",
            overall_ylabel = "Predicted",
            measerrfield = None,
            plot_filter_out = "",
            fit_only_on_matched_groups = 0,
            *args, **kwargs):
    """
        Fits on data and extrapolates prediction on 
        topredict_data and standard_conditions.
        Args:
            model: model to use
            data <data_parser data object>: data for fitting
            topredict_data_csv <str>: csv name for dataset for predictions
                            (to replace "lwr_data")
            standard_conditions_csv <str>: csv name for dataset of 
                                standard conditions, especially to be used 
                                if there are not enough points
                                in topredict_data_csv
            group_field_name <str>: field name for grouping total fit results
            label_field_name <str>: field name for labels of grouping
            xfield <str>: field name for x value to plot fit results against
            xlabel <str>: x-axis label for individual plots
            ylabel <str>: y-axis label for individual plots
            overall_xlabel <str>: x-axis label for overall plot
            overall_ylabel <str>: y-axis label for overall plot
            measerrfield <str>: field name for measured error in topredict_data,
    """
    fit_Xdata = np.asarray(data.get_x_data())
    fit_ydata = np.asarray(data.get_y_data()).ravel()

    pd_path = os.path.abspath(topredict_data_csv) 
    topredict_data = data_parser.parse(pd_path)
    topredict_data.set_y_feature(data.y_feature) #same feature as fitting data 
    topredict_data.set_x_features(data.x_features)#same features as fitting data
    topredict_Xdata = np.asarray(topredict_data.get_x_data())
    topredict_ydata = np.asarray(topredict_data.get_y_data()).ravel()
    if not (measerrfield == None):
        topredict_ydata_err = np.asarray(topredict_data.get_data(measerrfield)).ravel()
    else:
        topredict_ydata_err = np.zeros(len(topredict_ydata))

    if not (standard_conditions_csv== None):
        std_path = os.path.abspath(standard_conditions_csv)
        std_data = data_parser.parse(std_path)
        std_data.set_y_feature(xfield) #dummy y feature
        std_data.set_x_features(data.x_features)
        std_Xdata = np.asarray(std_data.get_x_data())
    else:
        std_Ypredict = None
        std_data = None
    
    fit_indices = gttd.get_field_logo_indices(data, group_field_name)
    fit_groups = list(fit_indices.keys())
    topredict_indices = gttd.get_field_logo_indices(topredict_data, group_field_name)
    topredict_groups = list(topredict_indices.keys())
    match_groups = np.intersect1d(fit_groups, topredict_groups)

    if int(fit_only_on_matched_groups) == 1:
        fit_index=list()
        for mgroup in match_groups:
            fit_index.extend(fit_indices[mgroup]["test_index"])
        fit_Xdata = fit_Xdata[fit_index]
        fit_ydata = fit_ydata[fit_index]

    supported_index=list()
    unsupported_index=list()
    for pgroup in topredict_groups:
        if pgroup in match_groups:
            supported_index.extend(topredict_indices[pgroup]["test_index"])
        else:
            unsupported_index.extend(topredict_indices[pgroup]["test_index"])

    model.fit(fit_Xdata, fit_ydata)
    #note that plot_filter_out only affects the plotting, not the model fitting

    Ypredict = model.predict(topredict_Xdata)
    
    if not (std_data == None):
        std_Ypredict = model.predict(std_Xdata)
   
    overall_rms = np.sqrt(mean_squared_error(topredict_ydata, Ypredict))
    supported_rms = np.sqrt(mean_squared_error(topredict_ydata[supported_index],
                    Ypredict[supported_index]))
    unsupported_rms = np.sqrt(mean_squared_error(topredict_ydata[unsupported_index],
                    Ypredict[unsupported_index]))
    notelist=list()
    notelist.append("Overall RMSE: %3.2f" % overall_rms)
    notelist.append("Supported RMSE: %3.2f" % supported_rms)
    notelist.append("Unsupported RMSE: %3.2f" % unsupported_rms)

    kwargs=dict()
    kwargs['xlabel'] = overall_xlabel
    kwargs['ylabel'] = overall_ylabel
    kwargs['savepath'] = savepath
    kwargs['xerr_supported'] = topredict_ydata_err[supported_index]
    kwargs['xerr_unsupported'] = topredict_ydata_err[unsupported_index]
    kwargs['notelist'] = notelist

    plotpm.single_supported_unsupported(topredict_ydata[supported_index], 
                    Ypredict[supported_index],
                    topredict_ydata[unsupported_index],
                    Ypredict[unsupported_index],
                    **kwargs)

    
    #from plot_data import plot_by_groups as pbg
    #pbg.plot_overall(fit_data=data, 
    #                topred_data=topredict_data,
#                    std_data=std_data,
#                    topred_Ypredict=Ypredict,
#                    std_Ypredict=std_Ypredict,
#                    group_field_name=group_field_name,
#                    label_field_name=label_field_name,
#                    xlabel=overall_xlabel,
#                    ylabel=overall_ylabel,
#                    xfield=xfield,
#                    measerrfield=measerrfield,
#                    plot_filter_out=plot_filter_out,
#                    only_fit_matches=0)
#    
#    pbg.plot_overall(fit_data=data, 
#                    topred_data=topredict_data,
#                    std_data=std_data,
#                    topred_Ypredict=Ypredict,
#                    std_Ypredict=std_Ypredict,
#                    group_field_name=group_field_name,
#                    label_field_name=label_field_name,
#                    xlabel=overall_xlabel,
#                    ylabel=overall_ylabel,
#                    xfield=xfield,
#                    measerrfield=measerrfield,
#                    plot_filter_out=plot_filter_out,
#                    only_fit_matches=1)
#    
#    pbg.plot_overall(fit_data=data, 
#                    topred_data=topredict_data,
#                    std_data=std_data,
#                    topred_Ypredict=Ypredict,
#                    std_Ypredict=std_Ypredict,
#                    group_field_name=group_field_name,
#                    label_field_name=label_field_name,
#                    xlabel=overall_xlabel,
#                    ylabel=overall_ylabel,
#                    xfield=xfield,
#                    measerrfield=measerrfield,
#                    plot_filter_out=plot_filter_out,
#                    only_fit_matches=2)
#
    #
    #pbg.plot_separate_groups_vs_xfield(fit_data=data, 
    #                topred_data=topredict_data,
    #                std_data=std_data,
    #                topred_Ypredict=Ypredict,
    #                std_Ypredict=std_Ypredict,
    #                group_field_name=group_field_name,
    #                label_field_name=label_field_name,
    #                xlabel=xlabel,
    #                ylabel=ylabel,
    #                xfield=xfield,
    #                plot_filter_out=plot_filter_out)
    return
