pymodaq_plugins_holoeye (HoloEye Instruments)
#############################################

.. the following must be adapted to your developped package, links to pypi, github  description...

.. image:: https://img.shields.io/pypi/v/pymodaq_plugins_holoeye.svg
   :target: https://pypi.org/project/pymodaq_plugins_holoeye/
   :alt: Latest Version

.. image:: https://readthedocs.org/projects/pymodaq/badge/?version=latest
   :target: https://pymodaq.readthedocs.io/en/stable/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_holoeye/workflows/Upload%20Python%20Package/badge.svg
   :target: https://github.com/PyMoDAQ/pymodaq_plugins_holoeye
   :alt: Publication Status

Set of PyMoDAQ plugins for Spatial Light Modulators (SLM) from Holoeye


Authors
=======

* Sebastien J. Weber  (sebastien.weber@cemes.fr)


Instruments
===========

Below is the list of instruments included in this plugin

Actuators
+++++++++

* **Holoeye**: load a DataActuator (should be used from an external application creating the complex 2D DataActuator)
* **HoloeyeFile**: Used to load phase data into the SLM from a file
* **HoloeyeSplitScreen**: Used to load a binary phase mask into the SLM and control both the
  split ratio (percentage of vertical/horizontal screen size) and the grey level in each part of the screen.

Infos
=====

The SDK from Holoeye is required to operate those plugins. All plugins can also receive a numpy
array directly to be loaded into the SLM. Working with **SLM Display SDK (Python) < 4.0.0**
