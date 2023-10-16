"""

.. _ref_plot_unfolding:

Unfolding Band Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unfolding Band Structure example.

First download the example files with the code below. Then replace data_dir below.

.. code-block::
   :caption: Downloading example

    supercell_dir = pyprocar.download_example(save_dir='', 
                                material='MgB2',
                                code='vasp', 
                                spin_calc_type='non-spin-polarized',
                                calc_type='supercell_bands')

    primitive_dir = pyprocar.download_example(save_dir='', 
                                material='MgB2',
                                code='vasp', 
                                spin_calc_type='non-spin-polarized',
                                calc_type='primitive_bands')
"""

###############################################################################
# importing pyprocar and specifying local data_dir
import os
import pyprocar

import numpy as np

supercell_dir = f"{pyprocar.utils.ROOT}{os.sep}data{os.sep}examples{os.sep}MgB2_unfold{os.sep}vasp{os.sep}non-spin-polarized{os.sep}supercell_bands"
primitive_dir = f"{pyprocar.utils.ROOT}{os.sep}data{os.sep}examples{os.sep}MgB2_unfold{os.sep}vasp{os.sep}non-spin-polarized{os.sep}primitive_bands"


###############################################################################
# Plotting primitive bands
# +++++++++++++++++++++++++++++++++++++++

pyprocar.bandsplot(
                code='vasp', 
                mode='plain',
                elimit=[-15,5],
                dirname=primitive_dir)


###############################################################################
# Unfolding of the supercell bands
# +++++++++++++++++++++++++++++++++++++++
#
# Here we do unfolding of the supercell bands. In this calculation, 
# the POSCAR and KPOINTS will be different from the primitive cell
# For the POSCAR, we create a 2 2 2 supercell from the primitive.
# For the KPOINTS, the paths need to be changed to reflect the change in the unitcell

pyprocar.unfold(
        code='vasp',
        mode='plain',
        unfold_mode='both',
        dirname= supercell_dir,
        elimit=[-15,5],
        supercell_matrix=np.diag([2, 2, 2]))
        
        