import inspect
import shutil
import subprocess

from pippin.base import ConfigBasedExecutable
from pippin.config import chown_dir, mkdirs, get_config
import os


class BiasCor(ConfigBasedExecutable):
    def __init__(self, name, output_dir, dependencies, options, merged_data, merged_iasim, merged_ccsim, classifier):
        self.data_dir = os.path.dirname(inspect.stack()[0][1]) + "/data_files/"
        super().__init__(name, output_dir, os.path.join(self.data_dir, "bbc.input"), "=", dependencies=dependencies)

        self.options = options
        self.logging_file = os.path.join(self.output_dir, "output.log")
        self.global_config = get_config()

        self.merged_data = merged_data
        self.merged_iasim = merged_iasim
        self.merged_ccsim = merged_ccsim

        self.bias_cor_fits = None
        self.cc_prior_fits = None
        self.data = None
        self.genversion = "_".join([m.get_lcfit_dep()["sim_name"] for m in merged_data]) + "_" + classifier.name

        self.config_path = f"{self.output_dir}/{self.genversion}.input"  # Make sure this syncs with the tmp file name

        self.probability_column_name = classifier.output["prob_column_name"]

    def _check_completion(self, squeue):
        pass

    def write_input(self, force_refresh):
        self.bias_cor_fits = ",".join([m.output["fitres_file"] for m in self.merged_iasim])
        self.cc_prior_fits = ",".join([m.output["fitres_file"] for m in self.merged_ccsim])
        self.data = [m.output["fitres_dir"] for m in self.merged_data]

        self.set_property("simfile_biascor", self.bias_cor_fits)
        self.set_property("simfile_ccprior", self.cc_prior_fits)
        self.set_property("varname_pIa", self.probability_column_name)
        self.set_property("OUTDIR_OVERRIDE", self.output_dir)

        final_output = "\n".join(self.base)

        new_hash = self.get_hash_from_string(final_output)
        old_hash = self.get_old_hash()

        if force_refresh or new_hash != old_hash:
            self.logger.debug("Regenerating results")

            shutil.rmtree(self.output_dir, ignore_errors=True)
            mkdirs(self.output_dir)

            with open(self.config_path, "w") as f:
                f.writelines(final_output)
            self.logger.info(f"Input file written to {self.config_path}")

            self.save_new_hash(new_hash)
            return True
        else:
            self.logger.debug("Hash check passed, not rerunning")
            return False

    def _run(self, force_refresh):
        regenerating = self.write_input(force_refresh)
        if regenerating:
            command = ["SALT2mu_fit.pl", self.config_path]
            for d in self.data:
                command += ["INPDIR+", d]
            command += ["NOPROMPT"]
            with open(self.logging_file, "w") as f:
                subprocess.run(command, stdout=f, stderr=subprocess.STDOUT, cwd=self.output_dir)
            chown_dir(self.output_dir)
        return True
