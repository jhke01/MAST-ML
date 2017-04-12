import matplotlib.pyplot as plt
import matplotlib
import data_parser
import numpy as np
import os
from sklearn.kernel_ridge import KernelRidge
from sklearn.metrics import mean_squared_error
import data_analysis.printout_tools as ptools
import portion_data.get_test_train_data as gttd
import FullFit
import plot_data.plot_xy as plotxy

def execute(model, data, savepath, 
        test_csv = None,
        standard_csv = None,
        group_field_name = None,
        label_field_name = None,
        numeric_field_name = None,
        xlabel="Measured",
        ylabel="Predicted",
        split_xlabel = "X",
        split_ylabel = "Prediction",
        stepsize=1,
        measured_error_field_name = None,
        plot_filter_out = "",
        fit_only_on_matched_groups = 0,
        *args,**kwargs):
    """Do full fit for extrapolation.
        test_csv <str>: test csv name
        standard_csv <str>: standard csv name
        group_field_name <str>: field name for grouping data
        label_field_name <str>: field name for labels corresponding to groups
        numeric_field_name <str>: field name for numeric data that will be used
                                    on the x-axis in per-group plots
        xlabel <str>: x-axis label for predicted-vs-measured plot
        ylabel <str>: y-axis label for predicted-vs-measured plot
        stepsize <float>: step size for predicted-vs-measured plot grid
        split_xlabel <str>: x-axis label for per-group plots of predicted and
                                measured y data versus data from field of
                                numeric_field_name
        split_ylabel <str>: y-axis label for per-group plots
        measured_error_field_name <str>: field name for measured y-data error (optional)
        plot_filter_out <str>: semicolon-delimited filters for plotting,
                                each a comma-delimited triplet, for example,
                                temperature,<,3000
                                See data_parser
        fit_only_on_matched_groups <int>: 1 - fit only on groups that exist
                                            in both the training data and
                                            the test_csv data
                                          0 - fit on all data in the training
                                                dataset (default)
                                        Only works if group_field_name is set.
    """
    stepsize=float(stepsize)
    #get datasets
    ##training
    train_xdata = np.asarray(data.get_x_data())
    train_ydata = np.asarray(data.get_y_data()).ravel()
    ##testing
    if test_csv == None:
        raise ValueError("test_csv is None")
    test_data = data_parser.parse(test_csv)
    if len(plot_filter_out) > 0:
        ftriplets = plot_filter_out.split(";")
        for ftriplet in ftriplets:
            fpcs = ftriplet.split(",")
            ffield = fpcs[0].strip()
            foperator = fpcs[1].strip()
            fval = fpcs[2].strip()
            try:
                fval = float(fval)
            except (ValueError, TypeError):
                pass
            test_data.add_exclusive_filter(ffield, foperator, fval)
    test_data.set_y_feature(data.y_feature) # same feature as fitting data
    test_data.set_x_features(data.x_features) # same features as fitting data
    test_xdata = np.asarray(test_data.get_x_data())
    test_ydata = np.asarray(test_data.get_y_data()).ravel()
    if numeric_field_name == None: #help identify each point
        numeric_field_name = data.x_features[0]
    # filter out for only matched groups
    if int(fit_only_on_matched_groups) == 1:
        if group_field_name == None:
            pass
        else:
            train_groupdata = np.asarray(data.get_data(group_field_name)).ravel()
            test_groupdata = np.asarray(test_data.get_data(group_field_name)).ravel()
            train_indices = gttd.get_logo_indices(train_groupdata)
            groups_not_in_test = np.setdiff1d(train_groupdata, test_groupdata)
            for outgroup in groups_not_in_test:
                data.add_exclusive_filter(group_field_name,"=",outgroup)
            train_xdata = np.asarray(data.get_x_data())
            train_ydata = np.asarray(data.get_y_data()).ravel()
    #
    kwargs_f = dict()
    kwargs_f['xlabel'] = xlabel
    kwargs_f['ylabel'] = ylabel
    kwargs_f['stepsize'] = stepsize
    kwargs_f['numeric_field_name'] = numeric_field_name
    kwargs_f['group_field_name'] = group_field_name
    kwargs_f['savepath'] = os.path.join(savepath,'test')
    if not (os.path.isdir(kwargs_f['savepath'])):
        os.mkdir(kwargs_f['savepath'])
    kwargs_f['do_pergroup_fits'] = 0 # NO per-group fitting
    kwargs_f['test_numericdata'] = np.asarray(test_data.get_data(numeric_field_name)).ravel()
    if not(group_field_name == None):
        kwargs_f['test_groupdata'] = np.asarray(test_data.get_data(group_field_name)).ravel()
        kwargs_f['train_groupdata'] = np.asarray(data.get_data(group_field_name)).ravel()
        if label_field_name == None:
            label_field_name = group_field_name
        kwargs_f['label_field_name'] = label_field_name
        kwargs_f['test_labeldata'] = np.asarray(test_data.get_data(label_field_name)).ravel()
    if not(measured_error_field_name == None):
        kwargs_f['test_yerrdata'] = np.asarray(test_data.get_data(measured_error_field_name)).ravel()
    kwargs_f['full_xtrain'] = train_xdata
    kwargs_f['full_ytrain'] = train_ydata
    kwargs_f['full_xtest'] = test_xdata
    kwargs_f['full_ytest'] = test_ydata
    test_data_array = FullFit.do_full_fit(model, **kwargs_f)
    
    ##standard has no y
    if not(standard_csv == None):
        std_data = data_parser.parse(standard_csv)
        if len(plot_filter_out) > 0:
            ftriplets = plot_filter_out.split(";")
            for ftriplet in ftriplets:
                fpcs = ftriplet.split(",")
                ffield = fpcs[0].strip()
                foperator = fpcs[1].strip()
                fval = fpcs[2].strip()
                try:
                    fval = float(fval)
                except (ValueError, TypeError):
                    pass
                std_data.add_exclusive_filter(ffield, foperator, fval)
        std_data.set_y_feature(data.x_features[0]) # dummy y feature
        std_data.set_x_features(data.x_features) # same features as fitting data
        std_xdata = np.asarray(std_data.get_x_data())
        std_ydata = np.asarray(std_data.get_y_data()).ravel()
        kwargs_s = dict()
        kwargs_s['xlabel'] = xlabel
        kwargs_s['ylabel'] = ylabel
        kwargs_s['stepsize'] = stepsize
        kwargs_s['numeric_field_name'] = numeric_field_name
        kwargs_s['group_field_name'] = group_field_name
        kwargs_s['savepath'] = savepath
        kwargs_s['savepath'] = os.path.join(savepath,'standard')
        if not (os.path.isdir(kwargs_s['savepath'])):
            os.mkdir(kwargs_s['savepath'])
        kwargs_s['fitlabel'] = "standard"
        kwargs_s['do_pergroup_fits'] = 0 # NO per-group fitting
        kwargs_s['test_numericdata'] = np.asarray(std_data.get_data(numeric_field_name)).ravel()
        if not(group_field_name == None):
            kwargs_s['test_groupdata'] = np.asarray(std_data.get_data(group_field_name)).ravel()
            kwargs_s['train_groupdata'] = np.asarray(std_data.get_data(group_field_name)).ravel()
            if label_field_name == None:
                label_field_name = group_field_name
            kwargs_s['label_field_name'] = label_field_name
            kwargs_s['test_labeldata'] = np.asarray(std_data.get_data(label_field_name)).ravel()
        kwargs_s['full_xtrain'] = train_xdata
        kwargs_s['full_ytrain'] = train_ydata
        kwargs_s['full_xtest'] = std_xdata
        kwargs_s['full_ytest'] = std_ydata
        std_data_array = FullFit.do_full_fit(model, **kwargs_s)
    else:
        std_data_array = None
    if numeric_field_name is None:
        return
    else:
        do_numeric_plots(test_data_array, std_data_array, split_xlabel, split_ylabel, savepath, group_field_name)
    return

def do_single_train_test_std_plot(train_x="", train_y="", test_x="", test_y="", 
                std_x=None, std_y=None, 
                xlabel="", ylabel="", savepath="", plotlabel=""):
    xdatalist=list()
    ydatalist=list()
    xerrlist=list()
    yerrlist=list()
    labellist=list()
    markers=""
    linestyles=""
    if not train_x is None:
        labellist.append("Measured")
        xdatalist.append(train_x)
        ydatalist.append(train_y)
        xerrlist.append(None)
        yerrlist.append(None)
        linestyles = linestyles + "None,"
        markers = markers + "o,"
    if not test_y is None:
        labellist.append("Predicted")
        xdatalist.append(test_x)
        ydatalist.append(test_y)
        xerrlist.append(None)
        yerrlist.append(None)
        linestyles = linestyles + "None,"
        markers = markers + "*,"
    if not std_x is None:
        labellist.append("Predicted")
        xdatalist.append(std_x)
        ydatalist.append(std_y)
        xerrlist.append(None)
        yerrlist.append(None)
        linestyles = linestyles + "-"
        markers = markers + "None"
    kwargs_p = dict()
    kwargs_p['savepath'] = os.path.join(savepath,"%s" % plotlabel)
    if not os.path.isdir(kwargs_p['savepath']):
        os.mkdir(kwargs_p['savepath'])
    kwargs_p['xlabel'] = xlabel
    kwargs_p['ylabel'] = ylabel
    kwargs_p['guideline'] = 0
    kwargs_p['linestyles'] = linestyles
    kwargs_p['markers'] = markers
    kwargs_p['sizes'] = "10,10,10"
    kwargs_p['faces'] = "None,None,None"
    kwargs_p['xdatalist'] = xdatalist
    kwargs_p['ydatalist'] = ydatalist
    kwargs_p['xerrlist'] = xerrlist
    kwargs_p['yerrlist'] = yerrlist
    kwargs_p['labellist'] = labellist
    kwargs_p['plotlabel'] = plotlabel
    plotxy.multiple_overlay(**kwargs_p)
    return
def do_numeric_plots(test_array, std_array, 
            xlabel,
            ylabel,
            savepath,group_field_name=None):
    if group_field_name == None:
        numidx=0
        gidx = -1
        lidx = -1
        midx = 1
        pidx = 2
    else:
        numidx=0
        gidx = 1
        lidx = 2
        midx = 3
        pidx = 4
    test_numericdata = test_array[:,numidx] #from FullFit
    test_measured = test_array[:,midx]
    test_predicted = test_array[:,pidx]
    if std_array is None:
        std_numericdata = None
        std_predicted = None
    else:
        std_numericdata = std_array[:,numidx]
        std_predicted = std_array[:,pidx] #measured does not matter for standard
    do_single_train_test_std_plot(train_x = test_numericdata,
            train_y = test_measured,
            test_x = test_numericdata,
            test_y = test_predicted,
            std_x = std_numericdata,
            std_y = std_predicted,
            xlabel=xlabel,
            ylabel=ylabel,
            savepath=savepath,
            plotlabel="alldata")
    if group_field_name is None:
        return #no other plots to do
    test_groupdata = test_array[:,gidx] #group
    test_labeldata = test_array[:,lidx]
    test_indices = gttd.get_logo_indices(test_groupdata)
    test_groups = list(test_indices.keys())
    if std_array is None:
        all_groups = np.copy(test_groups)
        std_groups = list()
    else:
        std_labeldata = std_array[:,lidx]
        std_groupdata = std_array[:,gidx]
        std_indices = gttd.get_logo_indices(std_groupdata)
        std_groups = list(std_indices.keys())
        all_groups = np.union1d(test_groups, std_groups)
    for group in all_groups:
        if not group in test_groups:
            test_index = list()
        else:
            test_index = test_indices[group]["test_index"]
            label = test_labeldata[test_index[0]]
        if not group in std_groups:
            std_index = list()
        else:
            std_index = std_indices[group]["test_index"]
            label = std_labeldata[std_index[0]]
        trainx = test_numericdata[test_index]
        trainy = test_measured[test_index]
        testx = test_numericdata[test_index]
        testy = test_predicted[test_index]
        if std_array is None:
            stdx = None
            stdy = None
        else:
            stdx = std_numericdata[std_index]
            stdy = std_predicted[std_index]
        do_single_train_test_std_plot(train_x = trainx, train_y = trainy,
                test_x = testx, test_y = testy,
                std_x = stdx, std_y = stdy,
                xlabel=xlabel,
                ylabel=ylabel,
                savepath=savepath,
                plotlabel=label)
    return


