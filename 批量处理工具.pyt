# -- coding:cp936 –

import arcpy
import os
import time
from arcpy import env
from arcpy.sa import *


def find_tifs(in_dir):
    # 返回当前文件夹（不包含子文件夹）in_dir中扩展名为.tif的文件的绝对路径构成的列表
    return [os.path.join(in_dir, fname) for fname in os.listdir(in_dir) if fname.endswith(".tif")]


def show_files(path, out_files, suffix=".tif", out_type="path"):
    file_list = os.listdir(path)
    for file in file_list:
        cur_path = os.path.join(path, file)
        if os.path.isdir(cur_path):
            show_files(cur_path, out_files, out_type=out_type)
        else:
            if file.endswith(suffix):
                if out_type == "path":
                    out_files.append(cur_path)
                elif out_type == "name":
                    out_files.append(file)
                else:
                    raise Exception("please select correct out_type value：path ；name")


def batch_func_raster(rasters, out_path, method, **params):
    """
    批量对多个栅格执行某个函数，并将处理后的栅格数据保存到out_path
    :param method: str
        要执行的某个函数的名称，该函数以*param为参数
    :param rasters:
    :param out_path:
    :param param：以字典形式向函数传递的多个参数
    :return:
    """
    nums = len(rasters)
    num = 1
    prefix = params.get("prefix")
    for raster in rasters:
        s = time.time()
        raster_name = os.path.split(raster)[1]
        out_raster = os.path.join(out_path, prefix + raster_name)
        if not os.path.exists(out_raster):
            try:
                if method == "times":
                    arcpy.gp.Times_sa(raster, params.get("scale_factor"), out_raster)
                if method == "setNull":
                    arcpy.gp.SetNull_sa(raster, raster, out_raster, params.get("condition"))
                if method == "resample":
                    arcpy.Resample_management(raster, out_raster, params.get("cell_size"), params.get("rs_type"))
                if method == "project":
                    arcpy.ProjectRaster_management(raster, out_raster, params["out_coor_system"],
                                                   params["resampling_type"], params["cell_size"],
                                                   "#", "#", "#")
                if method == "clip":
                    arcpy.Clip_management(raster, "#", out_raster, params["mask"], "#", "ClippingGeometry")
                if method == "aggregate":
                    arcpy.gp.Aggregate_sa(raster, out_raster, str(params["cell_factor"]), params["tech"], "EXPAND",
                                          "DATA")
                if method == "divide":
                    arcpy.gp.Divide_sa(raster, params["divide_factor"],out_raster)
                if method == "add":
                    arcpy.gp.Plus_sa(raster, params["add_factor"], out_raster)
                if method == "minus":
                    arcpy.gp.Minus_sa(raster, params["minus_factor"], out_raster)

                e = time.time()
                arcpy.AddMessage("%d/%d | %s completed, time used %.3fs" % (num, nums, out_raster, e - s))
            except Exception as err:
                arcpy.AddMessage("%d/%d | %s errored, %s" % (num, nums, out_raster, err))
        else:
            arcpy.AddMessage("%d/%d | %s already exists" % (num, nums, out_raster))
        num = num + 1


class Toolbox(object):
    def __init__(self):
        self.label = '批处理工具箱'
        self.alias = ''
        self.tools = [batchMathMultiply, batchSetnull, batchResample, batchReprojectRaster, batchClipRaster,
                      batchAggRaster, batchExtractSubdataset]
        # , batchClipRaster, batchSetnull,
        #           batchReprojectRaster, batchResample]


class batchMathMultiply(object):
    def __init__(self):
        self.label = '批量乘'
        self.name = 'batchMathMultiply'
        self.canRunInBackground = False

    def getParameterInfo(self):
        param_0 = arcpy.Parameter(name='raster_dir', displayName='raster_dir',
                                  datatype='Folder', parameterType='Required',
                                  direction='Input')
        param_1 = arcpy.Parameter(name='scale_factor', displayName='scale_factor',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_1.value = '0.0001'
        param_2 = arcpy.Parameter(name='new_dir_name', displayName='new_dir_name',
                                  parameterType='Required', direction='Input')
        param_2.value = 'multiplied'

        return [param_0, param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
                parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        if arcpy.CheckExtension("Spatial") != "Available":
            arcpy.AddMessage("Error!!! Spatial Analyst is unavailable")

        # get parameters, and create new folder
        in_path = parameters[0].valueAsText
        scale_factor = parameters[1].valueAsText
        new_folder_name = parameters[2].valueAsText
        rasters = find_tifs(in_path)
        out_path = os.path.join(in_path, new_folder_name)

        if not os.path.exists(out_path):
            os.mkdir(out_path)
        batch_func_raster(rasters, out_path, "times", scale_factor=scale_factor, prefix="scaled_")


class batchMathDivide(object):
    def __init__(self):
        self.label = '批量除'
        self.name = 'batchMathDivide'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # raster_dir
        param_0 = arcpy.Parameter(name='raster_dir', displayName='raster_dir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_1 = arcpy.Parameter(name='divide_factor', displayName='divide_factor',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_1.value = '1000'

        # new_dir_name
        param_2 = arcpy.Parameter(name='new_dir_name', displayName='new_dir_name',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_2.value = 'divided'
        return [param_0, param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        if arcpy.CheckExtension("Spatial") != "Available":
            arcpy.AddMessage("Error!!! Spatial Analyst is unavailable")

        # get parameters, and create new folder
        in_path = parameters[0].valueAsText
        divide_factor = parameters[1].valueAsText
        new_folder_name = parameters[2].valueAsText
        rasters = find_tifs(in_path)
        out_path = os.path.join(in_path, new_folder_name)

        if not os.path.exists(out_path):
            os.mkdir(out_path)
        batch_func_raster(rasters, out_path, "divide", divide_factor=divide_factor, prefix="divided_")


class batchMathAdd(object):
    def __init__(self):
        self.label = '批量加'
        self.name = 'batchMathAdd'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # raster_dir
        param_0 = arcpy.Parameter(name='raster_dir', displayName='raster_dir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_1 = arcpy.Parameter(name='add_factor', displayName='add_factor',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_1.value = 273.15
        param_2 = arcpy.Parameter(name='new_dir_name', displayName='new_dir_name',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_2.value = 'added'
        return [param_0, param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        if arcpy.CheckExtension("Spatial") != "Available":
            arcpy.AddMessage("Error!!! Spatial Analyst is unavailable")

        # get parameters, and create new folder
        in_path = parameters[0].valueAsText
        add_factor = parameters[1].valueAsText
        new_folder_name = parameters[2].valueAsText
        rasters = find_tifs(in_path)
        out_path = os.path.join(in_path, new_folder_name)

        if not os.path.exists(out_path):
            os.mkdir(out_path)
        batch_func_raster(rasters, out_path, "add", add_factor=add_factor, prefix="add_")


class batchMathMinus(object):
    def __init__(self):
        self.label = '开氏温度转摄氏度'
        self.name = 'batchMathMinus'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # raster_dir
        param_0 = arcpy.Parameter(name='raster_dir', displayName='raster_dir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_1 = arcpy.Parameter(name='minus_factor', displayName='minus_factor',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_1.value = 273.15
        param_2 = arcpy.Parameter(name='new_dir_name', displayName='new_dir_name',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_2.value = 'minused'
        return [param_0, param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        if arcpy.CheckExtension("Spatial") != "Available":
            arcpy.AddMessage("Error!!! Spatial Analyst is unavailable")

        # get parameters, and create new folder
        in_path = parameters[0].valueAsText
        minus_factor = parameters[1].valueAsText
        new_folder_name = parameters[2].valueAsText
        rasters = find_tifs(in_path)
        out_path = os.path.join(in_path, new_folder_name)

        if not os.path.exists(out_path):
            os.mkdir(out_path)
        batch_func_raster(rasters, out_path, "minus", minus_factor=minus_factor, prefix="minus_")



class batchSetnull(object):
    def __init__(self):
        self.label = '批量设为空'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # raster_dir
        param_0 = arcpy.Parameter(name='raster_dir', displayName='raster_dir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')

        # condition
        param_1 = arcpy.Parameter(name='condition', displayName='condition',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_1.value = 'VALUE<0'

        # new_dir_name
        param_2 = arcpy.Parameter(name='new_dir_name', displayName='new_dir_name',
                                  parameterType='Required',
                                  direction='Input')
        param_2.value = 'Setnulled'
        return [param_0, param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
                parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        in_path = parameters[0].valueAsText
        condition = parameters[1].valueAsText
        prefix = parameters[2].valueAsText

        rasters = find_tifs(in_path)
        out_path = os.path.join(in_path, "setN")
        if not os.path.exists(out_path):
            os.mkdir(out_path)

        if arcpy.CheckExtension("Spatial") == "Available":
            batch_func_raster(rasters, out_path, "setNull", condition=condition, prefix=prefix)


class batchResample(object):
    def __init__(self):
        self.label = '批量重采样栅格'
        self.canRunInBackground = False

    def getParameterInfo(self):
        param_0 = arcpy.Parameter(name='raster_dir', displayName='raster_dir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_1 = arcpy.Parameter(name='cell_size', displayName='cell_size',
                                  parameterType='Required', direction='Input',
                                  datatype='Cell Size XY')
        param_2 = arcpy.Parameter(name='resampling_type', displayName='resampling_type',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_2.value = 'NEAREST'
        param_2.filter.list = ['NEAREST', 'BILINEAR', 'CUBIC', 'MAJORITY']
        param_3 = arcpy.Parameter(name='new_dir_name', displayName='new_dir_name',
                                  parameterType='Optional', direction='Input',
                                  datatype='String')
        param_3.value = 'Resampled'
        return [param_0, param_1, param_2, param_3]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        in_path = parameters[0].valueAsText
        cell_size = parameters[1].valueAsText
        rs_type = parameters[2].valueAsText
        new_folder_name = parameters[3].valueAsText

        rasters = find_tifs(in_path)
        out_path = os.path.join(in_path, new_folder_name)
        if not os.path.exists(out_path):
            os.mkdir(out_path)

        batch_func_raster(rasters, out_path, "resample", prefix="rs_", cell_size=cell_size, rs_type=rs_type)


class batchReprojectRaster(object):
    def __init__(self):
        self.label = '批量投影栅格'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # raster_dir
        param_0 = arcpy.Parameter(name='raster_dir', displayName='raster_dir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_1 = arcpy.Parameter(name='out_coor_system', displayName='out_coor_system',
                                  parameterType='Required', direction='Input',
                                  datatype='File')
        param_1.filter.list = ["prj"]
        param_2 = arcpy.Parameter(name='resampling_type', displayName='resampling_type',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_2.value = 'NEAREST'
        param_2.filter.list = ['NEAREST', 'BILINEAR', 'CUBIC', 'MAJORITY']
        param_3 = arcpy.Parameter(name='cell_size', displayName='cell_size',
                                  parameterType='Optional', direction='Input',
                                  datatype='Cell Size XY')

        param_4 = arcpy.Parameter(name='new_dir_name', displayName='new_dir_name',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_4.value = 'Reprojected'
        return [param_0, param_1, param_2, param_3, param_4]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
                parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        # 允许覆盖地理处理操作
        env.overwriteOutput = False

        if arcpy.CheckExtension("Spatial") != "Available":
            arcpy.AddMessage("Error!!! Spatial Analyst is unavailable")

        in_path = parameters[0].valueAsText
        out_coor_system = parameters[1].valueAsText
        resampling_type = parameters[2].valueAsText
        cell_size = parameters[3].valueAsText
        new_folder_name = parameters[4].valueAsText

        rasters = find_tifs(in_path)
        out_path = os.path.join(in_path, new_folder_name)
        if not os.path.exists(out_path):
            os.mkdir(out_path)

        batch_func_raster(rasters, out_path, method="project", prefix="pr_", out_coor_system=out_coor_system,
                          resampling_type=resampling_type, cell_size=cell_size)


class batchClipRaster(object):
    def __init__(self):
        self.label = '批量裁剪栅格'
        self.name = 'atchClipRaster'
        self.canRunInBackground = False

    def getParameterInfo(self):
        param_0 = arcpy.Parameter(name='raster_dir', displayName='raster_dir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_1 = arcpy.Parameter(name='mask', displayName='mask',
                                  parameterType='Required', direction='Input',
                                  datatype='Shapefile')
        param_2 = arcpy.Parameter(name='new_dir_name', displayName='new_dir_name',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_2.value = 'Clip'
        return [param_0, param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        in_path = parameters[0].valueAsText
        mask = parameters[1].valueAsText
        new_folder_name = parameters[2].valueAsText

        rasters = find_tifs(in_path)
        out_path = os.path.join(in_path, new_folder_name)
        if not os.path.exists(out_path):
            os.mkdir(out_path)

        batch_func_raster(rasters, out_path, method="clip", prefix="clip_", mask=mask)


class batchAggRaster(object):
    def __init__(self):
        self.label = '批量聚合栅格'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # in_folder
        param_0 = arcpy.Parameter(name='in_folder', displayName='in_folder',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_1 = arcpy.Parameter(name='out_folder', displayName='out_folder',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_2 = arcpy.Parameter(name='cell_factor', displayName='cell_factor',
                                  parameterType='Required', direction='Input',
                                  datatype='Long')
        param_3 = arcpy.Parameter(name='prefix', displayName='prefix',
                                  parameterType='Required', direction='Input',
                                  datatype='String', )
        param_3.value = 'agg_'
        param_4 = arcpy.Parameter(name='tech', displayName='tech',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_4.filter.list = ['SUM', 'MAXIMUM', 'MEAN', 'MEDIAN', 'MINIMUM']
        return [param_0, param_1, param_2, param_3, param_4]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        arcpy.env.overwriteOutput = True

        in_path = parameters[0].valueAsText  # "X:\GLDAS_NOAH025"
        out_path = parameters[1].valueAsText  # "X:\GLDAS_NOAH025"
        cell_factor = parameters[2].valueAsText  # type:int
        prefix = parameters[3].valueAsText  # type:str
        tech = parameters[4].valueAsText  # aggreagation technique

        # Loop through a list of files in the workspace
        rasters = find_tifs(in_path)

        batch_func_raster(rasters, out_path, prefix=prefix, cell_factor=cell_factor, tech=tech)


class batchExtractSubdataset(object):
    def __init__(self):
        self.label = '批量提取波段数据集'
        self.canRunInBackground = True

    def getParameterInfo(self):
        # in_dir
        param_0 = arcpy.Parameter(name='in_dir', displayName='in_dir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_1 = arcpy.Parameter(name='out_dir', displayName='out_dir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_2 = arcpy.Parameter(name='subdataset_index', displayName='subdataset_index',
                                  parameterType='Optional', direction='Input',
                                  datatype='String')
        param_2.value = '0'
        param_3 = arcpy.Parameter(name='suffix', displayName='suffix',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_3.value = 'NDVI'
        return [param_0, param_1, param_2, param_3]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        in_path = parameters[0].valueAsText  # "X:\GLDAS_NOAH025"
        out_path = parameters[1].valueAsText  # "X:\GLDAS_NOAH025"
        sds_idx = parameters[2].valueAsText  # type:int
        suffix = parameters[3].valueAsText  # type:str

        arcpy.env.overwriteOutput = 1
        arcpy.CheckOutExtension("Spatial")

        arcpy.env.workspace = in_path
        arcpy.env.scratchWorkspace = in_path
        hdfList = arcpy.ListRasters('*', 'HDF')

        nums = len(hdfList)  # number of hdf files
        num = 1  # current serial number
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        for hdf in hdfList:
            s = time.time()
            raster_name = "{0}{1}{2}.{3}.tif".format(out_path, os.sep, '.'.join(hdf.split('.')[:3]), suffix)
            try:
                arcpy.ExtractSubDataset_management(hdf, raster_name, sds_idx)
                e = time.time()
                arcpy.AddMessage("%d/%d | %s Completed, time used %.3fs".format(num, nums, hdf, e - s))
            except:
                arcpy.AddMessage("%d/%d | %s Errored".format(num, nums, hdf))
            num += 1


class batchMosaic2(object):
    def __init__(self):
        self.label = '批量拼接栅格（不同区块）'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # in_dir
        param_0 = arcpy.Parameter(name='in_dir', displayName='in_dir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_1 = arcpy.Parameter(name='out_dir', displayName='out_dir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_2 = arcpy.Parameter(name='pixel_type', displayName='pixel_type',
                                  parameterType='Optional', direction='Input',
                                  datatype='String')
        param_2.value = '16_BIT_SIGNED'
        param_2.filter.list = ['1_BIT', '2_BIT', '4_BIT', '8_BIT_UNSIGNED ', '8_BIT_SIGNED', '16_BIT_UNSIGNED',
                               '16_BIT_SIGNED', '32_BIT_UNSIGNED', '32_BIT_SIGNED', '32_BIT_FLOAT', '64_BIT']
        param_3 = arcpy.Parameter(name='mosaic_method', displayName='mosaic_method',
                                  parameterType='Optional', direction='Input',
                                  datatype='String')
        param_3.value = 'MAXIMUM'
        param_3.filter.list = ['FIRST', 'LAST', 'BLEND', 'MEAN', 'MINIMUM', 'MAXIMUM', 'SUM']
        param_4 = arcpy.Parameter(name='colormap_mode', displayName='colormap_mode',
                                  parameterType='Optional', direction='Input',
                                  datatype='String', )
        param_4.value = 'FIRST'
        param_4.filter.list = ['FIRST', 'LAST', 'MATCH', 'REJECT']
        return [param_0, param_1, param_2, param_3, param_4]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        in_path = arcpy.GetParameterAsText(0)
        out_path = arcpy.GetParameterAsText(1)
        pixel_type = arcpy.GetParameterAsText(2)
        mosaic_method = arcpy.GetParameterAsText(3)
        colormap_mode = arcpy.GetParameterAsText(4)

        all_tifs = []
        groups = {}
        show_files(in_path, all_tifs, out_type="name")
        arcpy.env.workspace = in_path

        base = all_tifs[0]
        out_coor_system = arcpy.Describe(base).spatialReference
        cell_width = arcpy.Describe(base).meanCellWidth
        band_count = arcpy.Describe(base).bandCount

        for i in all_tifs:
            filename = i
            k = '.'.join(filename.split('.')[:2]) + '.' + '.'.join(filename.split('.')[-2:])
            if k in groups:
                groups[k].append(i)
            else:
                groups[k] = []
                groups[k].append(i)

        nums = len(groups)
        num = 1
        for i in groups:
            s = time.time()
            groups[i] = ';'.join(groups[i])
            if not os.path.exists(os.path.join(out_path, i)):
                arcpy.MosaicToNewRaster_management(groups[i], out_path, i, out_coor_system, pixel_type, cell_width,
                                                   band_count, mosaic_method, colormap_mode)
                e = time.time()
                arcpy.AddMessage("{0}/{1} | {2} Completed, time used {3}s".format(num, nums, i, e - s))
            else:
                e = time.time()
                arcpy.AddMessage("{0}/{1} | {2} existed, , time used {3}s".format(num, nums, i, e - s))
            num = num + 1


class batchRaster2Csv(object):
    def __init__(self):
        self.label = '批量导出栅格属性表'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # in_rasters
        param_0 = arcpy.Parameter(name='in_rasters', displayName='in_rasters',
                                  parameterType='Required', direction='Input',
                                  datatype='Raster Dataset', multiValue=True)
        param_1 = arcpy.Parameter(name='out_gdb', displayName='out_gdb',
                                  parameterType='Required', direction='Input',
                                  datatype=('Workspace', 'Raster Catalog'))
        param_2 = arcpy.Parameter(name='out_csv', displayName='out_csv',
                                  parameterType='Required', direction='Output',
                                  datatype='File')
        return [param_0, param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
                        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        # Script arguments
        in_rasters = parameters[0].valueAsText
        in_dbf = parameters[1].valueAsText
        out_csv = parameters[2].valueAsText
        messages.AddMessage(in_rasters)
        # Local variables:
        arcpy.RasterToGeodatabase_conversion(in_rasters, in_dbf, "")

        arcpy.env.workspace = in_dbf
        rasters = arcpy.ListRasters("*")
        for raster in rasters:
            rasloc = in_dbf + os.sep + raster
            fields = "*"
            try:
                lstFlds = arcpy.ListFields(rasloc)
                header = ''
                header += ",{0}".format(lstFlds[0].name) + ",{0}".format(lstFlds[1].name)
                if len(lstFlds) != 0:
                    f = open(out_csv, 'a')
                    header = header[0:] + ',RasterName\n'
                    f.write(header)
                    with arcpy.da.SearchCursor(rasloc, fields) as cursor:
                        for row in cursor:
                            f.write(str(row).replace("(", "").replace(")", "") + "," + raster + '\n')
                    f.close()
            except Exception as e:
                print(e)


class batchClipRaster2(object):
    def __init__(self):
        self.label = '批量裁剪栅格(多对多)'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Tifs
        param_0 = arcpy.Parameter(name='Tifs', displayName='Tifs',
                                  parameterType='Required', direction='Input',
                                  datatype='Raster Layer', multiValue=True)
        param_1 = arcpy.Parameter(name='Shapefiles', displayName='Shapefiles',
                                  parameterType='Required', direction='Input',
                                  datatype='Shapefile', multiValue=True)
        param_2 = arcpy.Parameter(name='Outfolder', displayName='Outfolder',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        return [param_0, param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        arcpy.env.parallelProcessingFactor = 0

        tifs = arcpy.GetParameterAsText(0)
        masks = arcpy.GetParameterAsText(1)
        out_dir = arcpy.GetParameterAsText(2)
        tifs = tifs.split(";")
        masks = masks.split(";")
        names = [os.path.splitext(os.path.basename(mask))[0] for mask in masks]

        size = len(tifs) * len(masks)
        num = 1
        for i, mask in enumerate(masks):
            # create a new folder named by mask's name
            new_folder = out_dir + os.sep + names[i]
            if not os.path.exists(new_folder):
                os.mkdir(new_folder)
            else:
                arcpy.AddMessage("Folder {0} already exists. Please check it.".format(new_folder))
            for tif in tifs:
                s = time.time()
                cliped_tif = os.path.join(new_folder, "{0}_{1}".format(names[i], os.path.split(tif)[1]))
                if not os.path.exists(cliped_tif):
                    arcpy.Clip_management(tif, "#", cliped_tif, mask, "#", "ClippingGeometry")
                    e = time.time()
                    arcpy.AddMessage("{0}/{1} | {2} Completed, time used {3}s".format(num, size, cliped_tif, e - s))
                else:
                    e = time.time()
                    arcpy.AddMessage("{0}/{1} | {2} already exists.".format(num, size, cliped_tif))
                num += 1


class batchCalFVC(object):
    def __init__(self):
        self.label = '批量估算植被覆盖度'
        self.canRunInBackground = False

    def getParameterInfo(self):
        param_0 = arcpy.Parameter(name='in_path', displayName='in_path',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_1 = arcpy.Parameter(name='out_path', displayName='out_path',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_2 = arcpy.Parameter(name='vi_soil', displayName='vi_soil',
                                  parameterType='Required', direction='Input',
                                  datatype='Any value')
        param_2.value = '0.1'
        param_3 = arcpy.Parameter(name='vi_veg', displayName='vi_veg',
                                  parameterType='Required', direction='Input',
                                  datatype='Any value', )
        param_3.value = '0.85'
        return [param_0, param_1, param_2, param_3]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        # Check out any necessary licenses
        arcpy.CheckOutExtension("spatial")
        in_path = arcpy.GetParameterAsText(0)
        out_path = arcpy.GetParameterAsText(1)
        vi_soil = arcpy.GetParameterAsText(2)
        vi_veg = arcpy.GetParameterAsText(3)

        arcpy.env.workspace = in_path
        # Local variables:
        tifs = [os.path.split(i)[1] for i in os.listdir(in_path) if i.endswith(".tif")]
        up = vi_soil
        lower = vi_veg
        vi_range = float(vi_veg) - float(vi_soil)
        for tif in tifs:
            condition = r"""Con(("{0}"<={1}),0,Con(("{0}">={2}),1,("{0}"-{1})/{3}))""".format(tif, up, lower, vi_range)
            arcpy.AddMessage(condition)
            out_tif = os.path.join(out_path, "{0}".format(tif.split(".")[0] + ".fc.tif"))
            arcpy.gp.RasterCalculator_sa(condition, out_tif)


class batchExtractByMask(object):
    def __init__(self):
        self.label = '批量按掩膜提取'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # in_folder
        param_0 = arcpy.Parameter(name='in_folder', displayName='in_folder',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_1 = arcpy.Parameter(name='in_raster', displayName='in_raster',
                                  parameterType='Required', direction='Input',
                                  datatype='Raster Dataset')
        param_2 = arcpy.Parameter(name='out_folder', displayName='out_folder',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        return [param_0, param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        in_folder = parameters[0].valueAsText
        input_raster = parameters[1].valueAsText
        out_folder = parameters[2].valueAsText

        # Input data source
        arcpy.env.workspace = in_folder
        arcpy.env.overwriteOutput = True

        # Loop through a list of files in the workspace
        tifs = [tif for tif in os.listdir(in_folder) if tif.endswith(".tif")]
        nums = len(tifs)
        for num, tif in enumerate(tifs):
            s = time.time()
            out_tif = os.path.join(out_folder, os.path.split(tif)[1])
            try:
                # Process:
                arcpy.gp.ExtractByMask_sa(tif, input_raster, out_tif)
                e = time.time()
                messages.AddMessage("{0}/{1} | {2} Completed, time used {3}s".format(num + 1, nums, tif, e - s))
            except:
                messages.AddMessage("{0}/{1} | {2} Errored".format(num + 1, nums, tif))


class esayMosaic(object):
    def __init__(self):
        self.label = '万能镶嵌工具'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # in_dir
        param_0 = arcpy.Parameter(name='in_dir', displayName='in_dir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_1 = arcpy.Parameter(name='out_dir', displayName='out_dir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_2 = arcpy.Parameter(name='pixel_type', displayName='pixel_type',
                                  parameterType='Optional', direction='Input',
                                  datatype='String')
        param_2.value = '16_BIT_SIGNED'
        param_2.filter.list = ['1_BIT', '2_BIT', '4_BIT', '8_BIT_UNSIGNED ', '8_BIT_SIGNED', '16_BIT_UNSIGNED',
                               '16_BIT_SIGNED', '32_BIT_UNSIGNED', '32_BIT_SIGNED', '32_BIT_FLOAT', '64_BIT']
        param_3 = arcpy.Parameter(name='mosaic_method', displayName='mosaic_method',
                                  parameterType='Optional', direction='Input',
                                  datatype='String', )
        param_3.value = 'LAST'
        param_3.filter.list = ['FIRST', 'LAST', 'BLEND', 'MEAN', 'MINIMUM', 'MAXIMUM', 'SUM']
        param_4 = arcpy.Parameter(name='colormap_mode', displayName='colormap_mode',
                                  parameterType='Optional', direction='Input',
                                  datatype='String')
        param_4.value = 'FIRST'
        param_4.filter.list = ['FIRST', 'LAST', 'MATCH', 'REJECT']

        return [param_0, param_1, param_2, param_3, param_4]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        pass


class batchFocalStats(object):
    def __init__(self):
        self.label = '批量焦点统计'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # in_folder
        param_0 = arcpy.Parameter(name='in_folder', displayName='in_folder',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_1 = arcpy.Parameter(name='out_folder', displayName='out_folder',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_2 = arcpy.Parameter(name='r', displayName='r',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_2.value = '250'
        return [param_0, param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        in_folder = parameters[0].valueAsText
        out_folder = parameters[1].valueAsText
        r = parameters[2].valueAsText

        # Input data source
        arcpy.env.workspace = in_folder
        arcpy.env.overwriteOutput = True

        # Loop through a list of files in the workspace
        tifs = [tif for tif in os.listdir(in_folder) if tif.endswith(".tif")]
        nums = len(tifs)
        for num, tif in enumerate(tifs):
            s = time.time()
            fileroot = tif[:-4] + "_f%s.tif" % r
            out_raster = out_folder + "/" + fileroot
            try:
                # Process:
                arcpy.gp.FocalStatistics_sa(tif, out_raster, "Circle {0} MAP".format(r), "MEAN", "DATA")
                e = time.time()
                messages.AddMessage("{0}/{1} | {2} Completed, time used {3}s".format(num + 1, nums, tif, e - s))
            except:
                messages.AddMessage("{0}/{1} | {2} Errored".format(num + 1, nums, tif))


class batchDefineProjection(object):
    def __init__(self):
        self.label = '批量定义投影WGS84'
        self.canRunInBackground = False

    def getParameterInfo(self):
        param_0 = arcpy.Parameter(name='indir', displayName='indir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        return [param_0]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        indir = parameters[0].valueAsText

        tifs = [os.path.join(indir, fn) for fn in os.listdir(indir) if fn.endswith(".tif")]
        out_corr = arcpy.SpatialReference("WGS 1984")
        nums = len(tifs)

        for num, tif in enumerate(tifs):
            s = time.time()
            try:
                # Process:
                arcpy.DefineProjection_management(tif, out_corr)
                e = time.time()
                messages.AddMessage("%d/%d | %s Completed, time used %.3fs".format(num + 1, nums, tif, e - s))
            except Exception as e:
                messages.AddMessage("%d/%d | %s Errored".format(num + 1, nums, tif))
                messages.AddMessage(e.message)


class createRetangleSHP(object):
    def __init__(self):
        self.label = '矢量文件生成扩大矩形边界'
        self.canRunInBackground = False

    def getParameterInfo(self):
        param_0 = arcpy.Parameter(name='shps', displayName='shps',
                                  parameterType='Required', direction='Input',
                                  datatype='Shapefile', multiValue=True)
        param_1 = arcpy.Parameter(name='outdir', displayName='outdir',
                                  parameterType='Required', direction='Input',
                                  datatype='Folder')
        param_2 = arcpy.Parameter(name='spacing', displayName='spacing',
                                  parameterType='Required', direction='Input',
                                  datatype='String')
        param_2.value = '0.2'
        return [param_0, param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        import arcgisscripting

        shps = parameters[0].valueAsText
        outdir = parameters[1].valueAsText
        spacing = float(parameters[2].valueAsText)

        shps = shps.split(";")

        def extents(fc):
            extent = arcpy.Describe(fc).extent
            west = extent.XMin
            south = extent.YMin
            east = extent.XMax
            north = extent.YMax
            return west, east, south, north

        def text_create(out_txt_path, msg):
            txt_file = open(out_txt_path, 'w')
            txt_file.write(msg)

        def rec_msg(xMin, yMin, xMax, yMax, spacing):
            x1, y1 = xMin - spacing, yMin - spacing
            x2, y2 = xMin - spacing, yMax + spacing
            x3, y3 = xMax + spacing, yMax + spacing
            x4, y4 = xMax + spacing, yMin - spacing
            return x1, y1, x2, y2, x3, y3, x4, y4

        for shp in shps:
            out_corr = arcpy.Describe(shp).spatialReference
            basename = os.path.basename(shp)[:-4]
            xMin, xMax, yMin, yMax = extents(shp)
            x1, y1, x2, y2, x3, y3, x4, y4 = rec_msg(xMin, yMin, xMax, yMax, spacing)
            msg = """Polygon
        0 0
        0 {0} {1} 1.#QNAN 1.#QNAN
        1 {2} {3} 1.#QNAN 1.#QNAN
        2 {4} {5} 1.#QNAN 1.#QNAN
        3 {6} {7} 1.#QNAN 1.#QNAN
        4 {0} {1} 1.#QNAN 1.#QNAN
        END""".format(x1, y1, x2, y2, x3, y3, x4, y4, x1, y1)

            out_txt = os.path.join(outdir, "%s.txt" % basename)
            text_create(out_txt, msg)

            gp = arcgisscripting.create()
            inSep = "."
            out_shp = os.path.join(outdir, "E_%s.shp" % basename)
            # out_coordinate_system = arcpy.SpatialReference('WGS 1984')
            gp.CreateFeaturesFromTextFile(out_txt, inSep, out_shp, out_corr)


class quickStats(object):
    def __init__(self):
        self.label = '统计栅格频率和累计频率'
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Input_raster
        param_0 = arcpy.Parameter(name='Input_raster', displayName='Input raster',
                                  parameterType='Required', direction='Input',
                                  datatype='Raster Layer')
        param_1 = arcpy.Parameter(name='Target_Acc_Pct', displayName='Target Acc Pct',
                                  parameterType='Required', direction='Input',
                                  datatype='Double', multiValue=True)
        param_1.value = '5;95'
        param_2 = arcpy.Parameter(name='Show_detail', displayName='Show detail',
                                  parameterType='Required', direction='Input',
                                  datatype='Boolean')
        param_2.value = 'false'
        return [param_0, param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        from collections import OrderedDict

        tif = parameters[0].valueAsText
        tar_accs = parameters[1].valueAsText  # List[float]
        show_detail = parameters[2]

        tar_accs = tar_accs.split(";")

        def searchNearIdx(in_arr, target):
            idx = 0
            active = 1
            while active and idx < len(in_arr):
                if in_arr[idx] > target:
                    active = 0
                else:
                    idx = idx + 1
            return idx

        def showInfo(raster_layer, show_detail=False):
            # read array from ASCII Grid File and use nodata value to filter array
            ndv = raster_layer.noDataValue
            arr_tmp = arcpy.RasterToNumPyArray(raster_layer.catalogPath)
            arr_valid = arr_tmp[arr_tmp != ndv]
            arr_valid.sort()
            res_count = OrderedDict()
            for i in arr_valid:
                if i not in res_count:
                    res_count[i] = 1
                else:
                    res_count[i] += 1
            arr_DN = list(res_count.keys())
            arr_Count = list(res_count.values())
            s = float(sum(arr_Count))
            arr_Percent = [(i / s * 100) for i in arr_Count]
            arr_Acc = [arr_Percent[0]]
            for v in arr_Percent[1:]:
                arr_Acc.append(v + arr_Acc[-1])
            if show_detail:
                messages.AddMessage("DN    COUNT    Percent    Acc Pct")
                infos = ["%5f    %d    %.6f    %.6f" % (vs[0], vs[1], vs[2], vs[3]) for vs in
                         zip(arr_DN, arr_Count, arr_Percent, arr_Acc)]
                messages.AddMessage("\n".join(infos))
            for tar in tar_accs:
                messages.AddMessage("==================================")
                tar_idx = searchNearIdx(arr_Acc, float(tar))
                messages.AddMessage("%.6f | %.6f | %.6f" % (float(tar), arr_Acc[tar_idx], arr_DN[tar_idx]))
                messages.AddMessage("DN    COUNT    Percent    Acc Pct")
                num = 5
                for i in range(tar_idx - num // 2, tar_idx + num // 2):
                    if 0 <= i < len(arr_DN):
                        messages.AddMessage(
                            "%5f    %d    %.6f    %.6f" % (arr_DN[i], arr_Count[i], arr_Percent[i], arr_Acc[i]))

        raster = arcpy.Raster(tif)
        if not raster.bandCount != 1:
            showInfo(raster, show_detail=show_detail)
        else:
            messages.AddMessage("%s is Multidimensional" % tif)
