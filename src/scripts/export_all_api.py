#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : export_all_api.py
@Date       : 2025/12/3 14:05
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: export_all_api
"""
from ..ctp import thostmduserapi as mdapi
from ..ctp import thosttraderapi as tdapi

with open("./mdapi.txt", "w+") as f:
    for method in dir(mdapi.CThostFtdcMdApi):
        f.write("- " + method + "\n")

with open("./mdspi.txt", "w+") as f:
    for method in dir(mdapi.CThostFtdcMdSpi):
        f.write("- " + method + "\n")

with open("./tdapi.txt", "w+") as f:
    for method in dir(tdapi.CThostFtdcTraderApi):
        f.write("- " + method + "\n")

with open("./tdspi.txt", "w+") as f:
    for method in dir(tdapi.CThostFtdcTraderSpi):
        f.write("- " + method + "\n")
