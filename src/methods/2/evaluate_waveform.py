#!python3

import os
import sys 
import numpy as np
import re

same_path_as_script = lambda filename: os.path.join(os.path.dirname(__file__), filename)
sys.path.append(same_path_as_script('../../'))
import wfa

import importlib
# import later: waveform_import
# import later: preprocess_data
	

class analysisData:
	def __init__(self):
		self.args = None
		self.CH = []
		# higher-level analysis description paramters and results in dictionary form
		self.hdr = {} # header data (dict)
		self.par = {} # analysis parameters (dict)
		self.res = {} # results (dict)
		self.err = {} # errors / quantities that failed to evaluate (contains defaults or NaN)

	def clean_up(self):
		for c in self.CH:
			del c
		self.CH  = []
		self.hdr = {} 
		self.par = {} 
		self.res = {}
		self.err = {}	
		

class analysisProcessor:
	
	def __init__(self, args):
		self.data = analysisData()
		self.data.args = args
		self.output_table_line_template = \
			'{success};{Modul};{Schalter};{R_shunt};"{file_base}";' + \
			'{V_CE_turnoff};{V_DC};{Ipk_turnoff};{Temp.};{RG};{V_GE_high};{V_GE_low};' + \
			'{turn_off_t1};{turn_off_t2};{turn_off_t3};{turn_off_t4};{turn_on_t1};{turn_on_t2};{turn_on_t3};{turn_on_t4};' + \
			'{E_turnoff_J};{E_turnon_J};{turn_off_t3};{turn_off_t4};' + \
			'{I_droop_during_pause};'	
		self.plotfile_template = same_path_as_script('../../setups/%s/gnuplot_template.plt' % args.setup)
		
	
	def extract_voltage_and_current_values(self):
		d = self.data
		
		print("\tvoltage and current levels")
		# extract basic waveform voltages and currents

		d.res['I_1st_fr_peak'] = d.CH[d.par['CH_ID']].percentile_value(d.par['tAOI_1st_fr_event'], 0.99)	
		d.res['V_D_1st_fr_peak'] = d.CH[d.par['CH_VD']].percentile_value(d.par['tAOI_1st_fr_event'], 0.99)	
		d.res['V_D_1st_on_av'] = d.CH[d.par['CH_VD']].average(d.par['tAOI_D_FWD'])[0]
		d.res['V_DC_1st_on_av'] = d.CH[d.par['CH_VDC']].average(d.par['tAOI_D_FWD'])[0]
		d.res['I_rr_fwd'] = d.CH[d.par['CH_ID']].percentile_value(d.par['tAOI_rr_event'], 0.995)
		d.res['I_rr_rev_max'] = d.CH[d.par['CH_ID']].percentile_value(d.par['tAOI_rr_event'], 0.001)		
		
		d.res['I_1st_on_fit_a_bx']  = d.CH[d.par['CH_ID']].lin_fit(d.par['tAOI_D_FWD'])
		I1 = lambda t, a=d.res['I_1st_on_fit_a_bx'][0], b=d.res['I_1st_on_fit_a_bx'][1] : [t, a + b*t]
		d.res['I_1st_fr_peak_lin_estimate'] = I1(d.par['t_1st_fall_nom'])
		d.res['I_rr_fwd_lin_estimate'] = I1(d.par['t_2nd_rise_nom'])
		# TODO	
				
			
	def extract_rr_timing_markers(self):
		# TODO
		return
		
		
	def calculate_rr_characteristics(self):
		# TODO
		return
		
			
	def print_assertion_error(self, error, full_info = False):
		print('\n\nAssertionError: ', error)
		if full_info:
			print('=============================================')
			visualize_output(purge_unresolved_placeholders = True)
			print('=============================================\n\n')	

			
		
	def store_header(self, fn):
		line = self.output_table_line_template.replace('"{','"').replace('}"','"').replace('{','"').replace('}','"') + '\n'
		if fn == None:
			print(line)
		else:
			f = open(fn, 'w')
			f.write(line)
			f.close()
		return


	def store_results(self, fn):
		line = self.resolve_placeholders(self.output_table_line_template) + '\n'
		if fn == None:
			print(line)
		else:
			f = open(fn, 'a')
			f.write(line)
			f.close()
		return
		
		
	def resolve_placeholders(self, s, purge_unresolved = False):
		d = self.data 
		
		for key in d.hdr.keys():
			s = s.replace('{%s}'%key, str(d.hdr[key]))
		for key in d.par.keys():
			s = s.replace('{%s}'%key, str(d.par[key]))
		for key in d.res.keys():
			s = s.replace('{%s}'%key, str(d.res[key]))
		for key in d.err.keys():
			s = s.replace('{%s}'%key, str(d.err[key]))	
		if purge_unresolved:
			placeholder_pattern = r'\{[^\}\/\\]*\}' # match "{text}" pattern except when text contains \ (gnuplot multiline) or / (gnuplot {/:bold ....} )
			s = re.sub(placeholder_pattern, '(nan)',s)
		return s
			
		
	def print_params_and_results(self):
		d = self.data 
	
		print("parameters:")
		for key in sorted(d.par.keys()):
			print("\t%s = %s" % (key, repr(d.par[key])))	
			
		print("results:")
		for key in sorted(d.res.keys()):
			print("\t%s = %s" % (key, repr(d.res[key])))
			
		if len(d.err) > 0:
			print("failed to evaluate:")
			for key in sorted(d.err.keys()):
				print("\t%s = %s" % (key, repr(d.err[key])))
			
		

	def visualize_output(self, purge_unresolved_placeholders = False):
		d = self.data 
	
		### generate output and gnuplot file for documentation
		
		self.print_params_and_results()
			
		d.par['insertion_before_plot'] = ''
		d.par['insertion_after_plot']  = ''
		
		if len(d.err) > 0:
			d.par['insertion_before_plot'] += 'set label 10000 "{/:Bold FAILED: %s}" font "Verdana,16" tc rgb "red" at graph 0.5, graph 0.5 center front\n' % (", ".join(d.err.keys()).replace('_', '\\\_'))
		
		# generate gnuplot script for visualization and validation
		f = open(self.plotfile_template, 'r', encoding='cp1252')
		plt = f.readlines()
		f.close()
		plt_output_filename = d.par['file_root'] + '.plt'
		f = open(plt_output_filename, 'w+')
		for line in plt: # replace all placeholders in the template file (same names as the dictionary keys) 
			f.write(self.resolve_placeholders(line, purge_unresolved_placeholders))
		f.close()
	
		
	def __process_file(self, filename):
	
		result = False
		
		headerlines = 22 # TODO: 
		self.data.par['header_rows'] = headerlines
		
		if waveform_import.read_file_header_and_data(filename, self.data):
			try: 
				preprocess_data.assign_advanced_analysis_parameters(self.data)
				preprocess_data.prepare_data(self.data)
				print("analysis:")
				self.extract_voltage_and_current_values()
			except AssertionError as e:
				self.print_assertion_error(e)
				return result

			result = True
			
			try: 
				self.extract_rr_timing_markers()
				self.calculate_rr_characteristics()
			except AssertionError as e:
				result = False
				self.print_assertion_error(e)
				
			self.data.res['success'] = int(len(self.data.err) == 0) # 1: success, 0: errors occured.
			self.visualize_output(purge_unresolved_placeholders = True)
			
		print("")
		return result
		
		
	def process_file(self, filename):
		global waveform_import, preprocess_data
		waveform_import   = importlib.import_module('formats.%s.waveform_import' % self.data.args.inputformat)
		preprocess_data   = importlib.import_module('setups.%s.preprocess_data'  % self.data.args.setup)
		
		print("processing:\n\t'%s'" % filename)
		
		preprocess_data.assign_basic_analysis_parameters(self.data)

		result = self.__process_file(filename)
			
		print("")
		return result
		
		
	def clean_up(self):
		self.data.clean_up()

		