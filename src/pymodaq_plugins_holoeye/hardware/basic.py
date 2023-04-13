# -*- coding: utf-8 -*-
"""
Created the 13/04/2023

@author: Sebastien Weber
"""
import pymodaq_plugins_holoeye  # mandatory if not imported from somewhere else to load holeye module from local install
from holoeye import slmdisplaysdk

# Open the SLM window:
slm = slmdisplaysdk.SLMInstance()

# Check if the library implements the required version
if not slm.requiresVersion(3):
    exit(1)

error = slm.open()
assert error == slmdisplaysdk.ErrorCode.NoError, slm.errorString(error)

# Unload the SDK:
slm = None