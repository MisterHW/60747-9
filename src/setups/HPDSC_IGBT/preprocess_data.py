import sys
import os
same_path_as_script = lambda filename: os.path.join(os.path.dirname(__file__), filename)
sys.path.append(same_path_as_script('../../'))
import wfa


def assign_basic_analysis_parameters(analysis_data):
	d = analysis_data
	
	### basic file information
	d.par['file_ext'] = '.txt'
	d.par['ndatacols'] = 4
	d.par['skipped_header_rows'] = 4
	d.par['R_shunt'] = 0.009888
	d.par['CH_VGE_raw'] = 0 # Channel 1 : gate-emitter voltage
	d.par['CH_VGE'] = d.par['CH_VGE_raw']
	d.par['CH_VDC_raw'] = 1 # Channel 2 : DC link voltage (uncorrected)
	# d.par['CH_VDC'] see prepare_data()
	d.par['CH_VCE_raw'] = 2 # Channel 3 : collector-shunt voltage (collector-emitter voltage + shunt and contact resistance dropout)
	d.par['CH_VCE'] = d.par['CH_VCE_raw']
	d.par['CH_IE_raw']  = 3 # Channel 4 : sensed current (shunt voltage * 100 A/V)
	d.par['CH_IE'] = d.par['CH_IE_raw']
	
	### detection parameters
	# 60747-9 calls for 0.02 (2% V_CE) which however excludes low voltage measurements.
	# Note high V_CE due to incomplete turn-on needs to be looked at separately and is not quantified by threshold crossing.
	d.par['DET_turn_on_t4_fraction'] = 0.05 
	# A more accurate intersection can be obtained by regression analysis over a fraction of some measure of the transition time.
	# This value is technology-, voltage- and temperature-dependent and 
	d.par['DET_turn_on_t4_refinement_time'] = 50E-9 
	
	
def assign_advanced_analysis_parameters(analysis_data):
	d = analysis_data
	
	print("parameters:")		
	# scope channel mapping
	d.par['TS_VGE'] = float(d.hdr['dt Cha.1 [Sek]']) # sampling time step 
	d.par['TS_VDC'] = float(d.hdr['dt Cha.2 [Sek]'])
	d.par['TS_VCE'] = float(d.hdr['dt Cha.3 [Sek]'])
	d.par['TS_IE']  = float(d.hdr['dt Cha.4 [Sek]'])
	# nominal gate driver timing
	d.par['t_1st_duration'] =  float(d.hdr['pre-charge [mS]']) * 1E-3
	d.par['t_inter_pulse_duration']   = float(d.hdr['pause [mS]']) * 1E-3
	d.par['t_2nd_duration'] =  float(d.hdr['puls [mS]' ]) * 1E-3
	assert d.par['t_1st_duration'] > 0, "\nduration needs to be positive, typically > 0.5E-6"
	assert d.par['t_inter_pulse_duration'] > 0, "\nduration needs to be positive, typically > 50E-6"
	assert d.par['t_2nd_duration'] > 0, "\nduration needs to be positive, typically > 5E-6"
	t_trigger = 0
	d.par['t_1st_rise_nom'] = t_trigger - d.par['t_inter_pulse_duration'] - d.par['t_1st_duration'] 
	d.par['t_1st_fall_nom'] = t_trigger - d.par['t_inter_pulse_duration']
	d.par['t_2nd_rise_nom'] = t_trigger # coincident with trigger (not accounting for propagation delay in the LWL and gate driver circuitry)
	d.par['t_2nd_fall_nom'] = t_trigger + d.par['t_2nd_duration']
	# switching event regions
	d.par['tAOI_turn_off_bounds'] = [d.par['t_1st_fall_nom'] - 0, d.par['t_1st_fall_nom'] + d.par['t_inter_pulse_duration'] * 0.9]
	d.par['tAOI_turn_off_bounds_begin'] = d.par['tAOI_turn_off_bounds'][0]
	d.par['tAOI_turn_off_bounds_end']   = d.par['tAOI_turn_off_bounds'][1]
	d.par['tAOI_turn_on_bounds']  = [d.par['t_2nd_rise_nom'] - 0.5E-6, d.par['t_2nd_rise_nom'] + d.par['t_2nd_duration'] * 0.9]
	d.par['tAOI_turn_on_bounds_begin'] = d.par['tAOI_turn_on_bounds'][0]
	d.par['tAOI_turn_on_bounds_end']   = d.par['tAOI_turn_on_bounds'][1]
	# analysis areas of interest (unit: seconds)
	assert d.par['t_1st_fall_nom'] < d.par['t_2nd_rise_nom']-22E-6, "\ntAOI_V_GE_low to be sampled within pause phase, equivalent to d.par['t_inter_pulse_duration'] > 22E-6"
	d.par['tAOI_V_GE_low']  = [d.par['t_2nd_rise_nom']-22E-6, d.par['t_2nd_rise_nom']- 2E-6] # AOI for off-state gate voltage estimation
	assert d.par['t_1st_rise_nom'] < d.par['t_1st_fall_nom']- 1.5E-6, "\ntAOI_V_GE_high to be sampled towards the end of the first pulse, equivalent to t_1st_duration > 1E-6 (pulse too short)"
	d.par['tAOI_V_GE_high'] = [d.par['t_1st_fall_nom']- 1E-6, d.par['t_1st_fall_nom']- 0] # AOI for on-state gate voltage estimation
	d.par['tAOI_V_DC'] = [d.par['t_1st_fall_nom'] + 5E-6, d.par['t_2nd_rise_nom'] - 2E-6] # AOI for DC link voltage estimation after first pulse
	assert d.par['tAOI_V_DC'][1] > d.par['tAOI_V_DC'][0], "invalid tAOI_V_DC interval. t_inter_pulse_duration too small or error in t_1st_fall_nom or t_2nd_rise_nom definitions."
	d.par['tAOI_V_CE'] = [d.par['t_1st_fall_nom'] - 2E-6, d.par['t_1st_fall_nom'] - 0E-6] # AOI for CE saturation voltage estimation close to peak current (not compensated for drop across shunt)
	assert  d.par['t_1st_fall_nom'] + 5E-6 < d.par['t_2nd_rise_nom'], "tAOI_Ipk_1st_fall overlaps second pulse / t_inter_pulse_duration < 5E-6."
	d.par['tAOI_Ipk_1st_fall'] = [d.par['t_1st_fall_nom'] - 0.5E-6, d.par['t_1st_fall_nom'] + 5E-6] # AOI for peak turn-off current detection
	assert d.par['t_2nd_rise_nom'] + 4E-6 < d.par['t_2nd_fall_nom'], "tAOI_Ipk_2nd_rise outside of second pulse / t_2nd_duration < 4E-6."
	d.par['tAOI_Ipk_2nd_rise'] = [d.par['t_2nd_rise_nom'] + 0, d.par['t_2nd_rise_nom'] + 4E-6] # AOI for peak turn-on current detection
	assert d.par['t_1st_duration'] > 0.5E-6, "tAOI_I_1st_fit requires tAOI_I_1st_fit > 0.5E-6"
	d.par['tAOI_I_1st_fit'] = [
		d.par['t_1st_fall_nom'] - max(min(10E-6, 0.8 * d.par['t_1st_duration']), 0.5E-6),
		d.par['t_1st_fall_nom'] - 0] # AOI for first pulse current rise (fit near end)
	assert d.par['t_2nd_rise_nom'] + 5E-6 < d.par['t_2nd_fall_nom'], "tAOI_I_2nd_fit exceeds beyond second pulse, t_2nd_duration > 5E-6 expected."
	d.par['tAOI_I_2nd_fit'] = [
		d.par['t_2nd_rise_nom'] + 4E-6,
		d.par['t_2nd_rise_nom'] + max(min(15E-6, 0.8 * d.par['t_2nd_duration']), 5E-6)] # AOI for second pulse current rise (fit near beginning)
		
		
		
def prepare_data(analysis_data):
	d = analysis_data
	
	# Note: files are not overwritten, all plots have to copy the following corrections.
	
	# apply real shunt value conversion factor (scope has been set up with 10mOhm nominal shunt resistance)
	d.CH[d.par['CH_IE']].multiply_by(1/(100.0 * d.par['R_shunt']))	
	
	# shunt and DC link capacitor are series connected 
	# * note: forward voltage is recorded as negative, current as positive
	# * subtract shunt voltage from VDC_raw
	
	V_DC_corrected = None
	
	if ( (d.CH[d.par['CH_VDC_raw']].timebase == d.CH[d.par['CH_IE']].timebase) and 
		(d.CH[d.par['CH_VDC_raw']].t0_samplepos == d.CH[d.par['CH_IE']].t0_samplepos) and 
		(len(d.CH[d.par['CH_VDC_raw']].s) == len(d.CH[d.par['CH_IE']].s)) ):
		# shortcut: work directly on the waveform data 
		# assuming channels have equal and aligned number of equidistant samples
		V_DC_corrected = d.CH[d.par['CH_VDC_raw']].s - d.par['R_shunt'] * d.CH[d.par['CH_IE']].s
	else:	
		# fallback: slow version with interpolation
		# create additional V_CE_corr waveform corrected for shunt dropout voltage
		shunt_dropout_correction =  lambda vals, R=d.par['R_shunt'] : vals[0] - R * vals[1]

		V_DC_corrected = wfa.arithmetic_operation(
			WFA_list = [d.CH[d.par['CH_VDC_raw']], d.CH[d.par['CH_IE']]], 
			tAOI = d.CH[d.par['CH_VDC_raw']].time_span(), 
			func = shunt_dropout_correction )[1]

	d.CH.append( wfa.WaveformAnalyzer(
		samples_data     = V_DC_corrected , 
		timebase         = d.CH[d.par['CH_VDC_raw']].timebase, 
		t0_samplepos     = d.CH[d.par['CH_VDC_raw']].t0_samplepos,
		timebase_unitstr = 's',
		id_str           = 'Channel %d (corr)' % (d.par['CH_VDC_raw']+1) ))
		
	# update channel reference
	d.par['CH_VDC'] = len(d.CH) - 1
