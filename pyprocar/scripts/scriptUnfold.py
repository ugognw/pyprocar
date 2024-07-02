import os
import yaml

import numpy as np

from pyprocar.cfg import ConfigFactory, ConfigManager, PlotType
from pyprocar.utils import welcome,ROOT
from pyprocar.utils.defaults import settings
from pyprocar.utils.info import orbital_names
from pyprocar.plotter import EBSPlot
from pyprocar import io


with open(os.path.join(ROOT,'pyprocar','cfg','unfold.yml'), 'r') as file:
    plot_opt = yaml.safe_load(file)

def unfold(
        code="vasp",
        dirname=".",
        mode="plain",
        unfold_mode="both",
        transformation_matrix=np.diag([2, 2, 2]),
        spins=None,
        atoms=None,
        orbitals=None,
        items=None,
        projection_mask=None,
        unfold_mask=None,
        fermi=None,
        fermi_shift=0,
        interpolation_factor=1,
        interpolation_type="cubic",
        vmax=None,
        vmin=None,
        kticks=None,
        knames=None,
        kdirect=True,
        elimit=None,
        ax=None,
        show=True,
        savefig=None,
        old=False,
        savetab="unfold_result.csv",
        print_plot_opts:bool=False,
        **kwargs,
):
    """

        Parameters
        ----------
        fname: PROCAR filename.
        poscar: POSCAR filename
        outcar: OUTCAR filename, for reading fermi energy. You can also use efermi and set outcar=None
        supercell_matrix: supercell matrix from primitive cell to supercell
        ispin: For non-spin polarized system, ispin=None.
           For spin polarized system: ispin=1 is spin up, ispin=2 is spin down.
        fermi: Fermi energy
        fermi_shift: Shift the bands by the Fermi energy.
        elimit: range of energy to be plotted.
        kticks: the indices of K points which has labels given in knames.
        knames: see kticks
        print_kpts: print all the kpoints to screen. This is to help find the kticks and knames.
        show_band: whether to plot the bands before unfolding.
        width: the width of the unfolded band.
        color: color of the unfoled band.
        savetab: the csv file name of which  the table of unfolding result will be written into.
        savefig: the file name of which the figure will be saved.
        exportplt: flag to export plot as matplotlib.pyplot object.

        """
    welcome()
    default_config = ConfigFactory.create_config(PlotType.BAND_STRUCTURE)
    config=ConfigManager.merge_configs(default_config, kwargs)
    modes_txt=' , '.join(config.modes)

    message=f"""
            --------------------------------------------------------
            There are additional plot options that are defined in a configuration file. 
            You can change these configurations by passing the keyword argument to the function
            To print a list of plot options set print_plot_opts=True

            Here is a list modes : {modes_txt}
            --------------------------------------------------------
            """
    print(message)
    if print_plot_opts:
        for key,value in plot_opt.items():
            print(key,':',value)
    
    parser = io.Parser(code = code, dir = dirname)
    ebs = parser.ebs
    structure = parser.structure
    kpath = parser.kpath

    if fermi is not None:
        ebs.bands -= fermi
        ebs.bands += fermi_shift
        fermi_level = fermi_shift
        y_label=r"E - E$_F$ (eV)"
    else:
        y_label=r"E (eV)"
        print("""
            WARNING : `fermi` is not set! Set `fermi={value}`. The plot did not shift the bands by the Fermi energy.
            ----------------------------------------------------------------------------------------------------------
            """)

    ebs_plot = EBSPlot(ebs, kpath, ax, spins, config=config)
    
    labels=None

    

    if mode is not None:
        if ebs.projected_phase is None :
            raise ValueError("The provided electronic band structure file does not include phases")
        ebs_plot.ebs.unfold(transformation_matrix=transformation_matrix, structure=structure)
    if unfold_mode == 'both':
        width_weights = ebs_plot.ebs.weights
        width_mask = unfold_mask
        color_weights = ebs_plot.ebs.weights
        color_mask = unfold_mask
    elif unfold_mode == 'thickness':
        width_weights = ebs_plot.ebs.weights
        width_mask = unfold_mask
        color_weights = None
        color_mask = None
    elif unfold_mode == 'color':
        width_weights=None
        width_mask=None
        color_weights = ebs_plot.ebs.weights
        color_mask = unfold_mask
    else :
        raise ValueError("Invalid unfold_mode was selected: {unfold_mode} please select from the following 'both', 'thickness','color'")
    labels = []
    if mode == "plain":
        ebs_plot.plot_bands()
        ebs_plot.plot_parameteric(color_weights=color_weights,
                width_weights=width_weights,
                color_mask=color_mask,
                width_mask=width_mask,
                spins=spins)
        ebs_plot.handles = ebs_plot.handles[:ebs_plot.nspins]
    elif mode in ["overlay", "overlay_species", "overlay_orbitals"]:
        weights = []


        if mode == "overlay_species":

            for ispc in structure.species:
                labels.append(ispc)
                atoms = np.where(structure.atoms == ispc)[0]
                w = ebs_plot.ebs.ebs_sum(
                    atoms=atoms,
                    principal_q_numbers=[-1],
                    orbitals=orbitals,
                    spins=spins,
                )
                weights.append(w)
        if mode == "overlay_orbitals":
            for iorb in ["s", "p", "d", "f"]:
                if iorb == "f" and not ebs_plot.ebs.norbitals > 9:
                    continue
                labels.append(iorb)
                orbitals = orbital_names[iorb]
                w = ebs_plot.ebs.ebs_sum(
                    atoms=atoms,
                    principal_q_numbers=[-1],
                    orbitals=orbitals,
                    spins=spins,
                )
                weights.append(w)

        elif mode == "overlay":
            if isinstance(items, dict):
                items = [items]

            if isinstance(items, list):
                for it in items:
                    for ispc in it:
                        atoms = np.where(structure.atoms == ispc)[0]
                        if isinstance(it[ispc][0], str):
                            orbitals = []
                            for iorb in it[ispc]:
                                orbitals = np.append(
                                    orbitals, orbital_names[iorb]
                                ).astype(np.int)
                            labels.append(ispc + "-" + "".join(it[ispc]))
                        else:
                            orbitals = it[ispc]
                            labels.append(ispc + "-" + "_".join(it[ispc]))
                        w = ebs_plot.ebs.ebs_sum(
                            atoms=atoms,
                            principal_q_numbers=[-1],
                            orbitals=orbitals,
                            spins=spins,
                        )
                        weights.append(w)
        ebs_plot.plot_parameteric_overlay(
            spins=spins, vmin=vmin, vmax=vmax, weights=weights
        )
    else:
        if atoms is not None and isinstance(atoms[0], str):
            atoms_str = atoms
            atoms = []
            for iatom in np.unique(atoms_str):
                atoms = np.append(atoms, np.where(structure.atoms == iatom)[0]).astype(
                    np.int
                )

        if orbitals is not None and isinstance(orbitals[0], str):
            orbital_str = orbitals

            orbitals = []
            for iorb in orbital_str:
                orbitals = np.append(orbitals, orbital_names[iorb]).astype(np.int)
        weights = ebs_plot.ebs.ebs_sum(
            atoms=atoms, principal_q_numbers=[-1], orbitals=orbitals, spins=spins
        )

        if settings.ebs.weighted_color:
            color_weights = weights
        else:
            color_weights = None
        if settings.ebs.weighted_width:
            width_weights = weights
        else:
            width_weights = None

        color_mask = projection_mask
        width_mask = unfold_mask
        width_weights = ebs_plot.ebs.weights
        if mode == "parametric":
            ebs_plot.plot_parameteric(
                color_weights=color_weights,
                width_weights=width_weights,
                color_mask=color_mask,
                width_mask=width_mask,
                spins=spins
            )
        elif mode == "scatter":
            ebs_plot.plot_scatter(
                color_weights=color_weights,
                width_weights=width_weights,
                color_mask=color_mask,
                width_mask=width_mask,
                spins=spins
            )

        else:
            print("Selected mode %s not valid. Please check the spelling " % mode)

    ebs_plot.set_xticks(kticks, knames)
    ebs_plot.set_yticks(interval=elimit)
    ebs_plot.set_xlim()
    ebs_plot.set_ylim(elimit)
    if fermi is not None:
        ebs_plot.draw_fermi(fermi_level=fermi_level)
    ebs_plot.set_ylabel(label=y_label)

    ebs_plot.grid()
    ebs_plot.legend(labels)
    if savefig is not None:
        ebs_plot.save(savefig)
    if show:
        ebs_plot.show()
    return ebs_plot.fig, ebs_plot.ax



#     if efermi is not None:
#         fermi = efermi
#     elif outcar is not None:
#         outcarparser = UtilsProcar()
#         fermi = outcarparser.FermiOutcar(outcar)
#     else:
#         raise Warning("Fermi energy is not given, neither an OUTCAR contains it.")

#     uf = ProcarUnfolder(
#         procar=fname, poscar=poscar, supercell_matrix=supercell_matrix, ispin=ispin
#     )
#     if print_kpts:
#         for ik, k in enumerate(uf.procar.kpoints):
#             print(ik, k)
#     axes = uf.plot(
#         efermi=fermi,
#         ispin=ispin,
#         shift_efermi=shift_efermi,
#         ylim=elimit,
#         ktick=kticks,
#         kname=knames,
#         color=color,
#         width=width,
#         savetab=savetab,
#         show_band=show_band,
#     )

#     if exportplt:
#         return plt

#     else:
#         if savefig:
#             plt.savefig(savefig, bbox_inches="tight")
#             plt.close()  # Added by Nicholas Pike to close memory issue of looping and creating many figures
#         else:
#             plt.show()
#         return


# # if __name__ == '__main__':
# #     """
# #     An example of how to use
# #     """
# #     import pyprocar
# #     import numpy as np
# #     pyprocar.unfold(
# #         fname='PROCAR',
# #         poscar='POSCAR',
# #         outcar='OUTCAR',
# #         supercell_matrix=np.diag([2, 2, 2]),
# #         efermi=None,
# #         shift_efermi=True,
# #         ispin=0,
# #         elimit=(-5, 15),
# #         kticks=[0, 36, 54, 86, 110, 147, 165, 199],
# #         knames=['$\Gamma$', 'K', 'M', '$\Gamma$', 'A', 'H', 'L', 'A'],
# #         print_kpts=False,
# #         show_band=True,
# #         savefig='unfolded_band.png')
