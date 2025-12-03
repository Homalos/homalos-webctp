#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: webctp
@FileName   : __init__.py.py
@Date       : 2025/12/2 18:13
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: description
"""
# start delvewheel patch
def _delvewheel_patch_1_11_1():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'libs'))):
        os.add_dll_directory(libs_dir)
        print(f'Adding {libs_dir} to DLL search path')
        os.add_dll_directory(libs_dir)
    else:
        raise RuntimeError('Cannot find libs directory')


_delvewheel_patch_1_11_1()
del _delvewheel_patch_1_11_1
# end delvewheel patch

# Note: Do not import thostmduserapi and thosttraderapi here to avoid circular imports
# Users should import them directly: from ctp import thostmduserapi, thosttraderapi
# or: import ctp.thostmduserapi as mdapi
