#!python3

import numpy as np

class WaveformAnalyzer:
	s = []; # 1D sample data
	timebase = 1.0
	timebase_unitstr = 'a.u.'
	id_str = 'waveform'
	t0_samplepos = 0
	
	
	def __init__(self, samples_data, 
			timebase = timebase, t0_samplepos = t0_samplepos, 
			timebase_unitstr = timebase_unitstr, id_str = id_str):
			
		self.s = samples_data
		self.timebase = timebase
		self.t0_samplepos = t0_samplepos 
		self.timebase_unitstr = timebase_unitstr
		self.id_str = id_str 
		
		
	def multiply_by(self, f):
		self.s = self.s * f
		
		
	def invert(self):
		self.s = self.s * -1
		
		
	def __force_inrange(self, sAOI):
		initial_sAOI = sAOI
		for i in range(0, len(sAOI)):
			sAOI[i] = max(0, min(len(self.s)-1, sAOI[i]))
		if sAOI != initial_sAOI:
			print("warning: sample AOI out of range. Values changed from" + 
					repr(initial_sAOI) + " to " + repr(sAOI))
					
		
	def smp_to_time(self, sAOI):
		# self.__force_inrange(sAOI) # not used, time values are not directly used with self.s
		smp_to_t = lambda s: (s - self.t0_samplepos) * self.timebase
		tAOI = [smp_to_t(sAOI[i]) for i in range(0, len(sAOI))]
		return tAOI
	
	
	def time_to_smp(self, tAOI, force_inrange = True):
		t_to_smp = lambda t: t / self.timebase + self.t0_samplepos
		sAOI = [t_to_smp(tAOI[i]) for i in range(0, len(tAOI))]
		if force_inrange:
			self.__force_inrange(sAOI)
		return sAOI
		
	def time_span(self):
		return self.smp_to_time([0,len(self.s)-1])
		
		
	def sum(self, tAOI):
		sAOI = list(map(lambda x: int(round(x)), self.time_to_smp(tAOI)))
		tAOI_adj = self.smp_to_time(sAOI)
		nsmp = sAOI[1] - sAOI[0] + 1
		wfmsum = np.sum(self.s[sAOI[0]:sAOI[1]])
		return [wfmsum, nsmp, tAOI_adj[0], tAOI_adj[1]]
		
		
	def average(self, tAOI):
		wfmsum, nsmp, t_begin, t_end = self.sum(tAOI)
		return [wfmsum/nsmp, nsmp, t_begin, t_end]
		
	def integral(self, tAOI):
		wfmsum, nsmp, t_begin, t_end = self.sum(tAOI)
		return [wfmsum*(t_end - t_begin)/nsmp, nsmp, t_begin, t_end]
		
		
	def sorted_points(self, tAOI):
		sAOI = self.time_to_smp(tAOI)
		y = self.s[int(round(sAOI[0])):int(round(sAOI[1]))]
		x = self.samples_t(tAOI, len(y))
		indices = np.argsort(y)
		return np.array(list(zip(x[indices],y[indices]))) 


	def samples_in_AOI(self, tAOI):
		sAOI = self.time_to_smp(tAOI)
		y = self.s[int(round(sAOI[0])):int(round(sAOI[1]))]
		x = self.samples_t(tAOI, len(y))
		return [x, y]	
		
		
	def sorted_samples(self, tAOI):
		sAOI = self.time_to_smp(tAOI)
		return np.sort(self.s[round(sAOI[0]):round(sAOI[1])]) # quicksort ascending		
		
	
	def overlaps(self, tAOI):	
		sAOI = self.time_to_smp(tAOI)
		return (sAOI[1] > sAOI[0])
		
		
	def percentile_values(self, tAOI, percentiles):
		sorted_samples = self.sorted_samples(tAOI)
		nsmp = len(sorted_samples)
		if nsmp == 0:
			print("Error in wfa.percentile_values() : 0 samples in range.")
			return None
		else:
			return [ sorted_samples[max(0, min(round((nsmp-1)*p), nsmp-1))] for p in percentiles ]
		
		
	def sorted_samples_in_rect(self, tAOI, yAOI):
		points_in_tAOI = self.sorted_points(tAOI)
		idx0 = next(idx for idx, item in enumerate(points_in_tAOI) if item[1] > yAOI[0])
		idx1 = next(idx for idx, item in enumerate(points_in_tAOI) if item[1] > yAOI[1])
		return points_in_tAOI[min(idx0, idx1): max(idx0, idx1)]
		
		
	def percentile_value(self, tAOI, percentile):
		return self.percentile_values(tAOI, [percentile])[0]
		
		
	def samples_t(self, tAOI, nsmp = 0):
		if nsmp < 0:
			raise ValueError("nsmp < 0")
			return []
		sAOI = list(map(lambda x:int(round(x)), self.time_to_smp(tAOI)))
		if nsmp == 0:
			nsmp = sAOI[1] - sAOI[0] + 1
		return np.linspace(start = tAOI[0], stop = tAOI[1] , num = nsmp)
		
		
	def lin_fit(self, tAOI):
		a, b, success = 0, 0, False # polynomial coefficients for p(x) * a + b*x and success result
		sAOI = list(map(lambda x:int(round(x)), self.time_to_smp(tAOI)))
		s_y = self.s[int(sAOI[0]):int(sAOI[1])+1]
		nsmp = len(s_y)
		if nsmp > 1:
			# formula: https://en.wikipedia.org/wiki/Simple_linear_regression
			s_x = self.samples_t(tAOI)	
			mean_x = np.mean(s_x)
			mean_y = np.mean(s_y)
			cov_matrix = np.cov(s_x, s_y) 
			cov_xy = cov_matrix[0][1]
			var_x  = cov_matrix[0][0]
			b = cov_xy / var_x
			a = mean_y - b * mean_x
			success = True
		else: 
			a = s_y[0]
			b = 0
			success = False 
		return [a,b, success]
		
		
	def find_level_crossing(self, tAOI, level, edge='both', t_edge=0, right_to_left = False):
		### find level crossing through <edge> within a <time AOI> region
		edge_both = edge != 'rising' and edge != 'falling'
		# t_edge helps define the minimum number of samples for threshold detection
		tau_samples  = 1 # relevant timescale of the transition around trigger
		if (t_edge > self.timebase) and (self.timebase > 0):
			tau_samples = np.ceil(t_edge/self.timebase)
		# prepare data 
		sAOI = list(map(lambda x : int(round(x)), self.time_to_smp(tAOI)))
		s_y = self.s[sAOI[0]:sAOI[1]+1]
		#	detect edge
		# see https://dsp.stackexchange.com/questions/30039/detect-to-rising-stable-and-falling-point-in-non-smooth-rectangular-wave ?
		# see http://chamilo2.grenet.fr/inp/courses/ENSE3A35EMIAAZ0/document/change_detection.pdf
		prelim_trig_x = None # index of element at level crossing
		threshold = np.full((1,len(s_y)), level)
		s_y_above = np.greater(s_y, threshold)[0].tolist()

		changed_state = None 
		if edge_both:
			changed_state = not s_y_above
		if edge == 'rising':
			changed_state = True
		if edge == 'falling':
			changed_state = False
		try:
			if right_to_left:
				s_y_above.reverse()
				prelim_trig_x = (len(s_y_above) - 1) - s_y_above.index(not changed_state) - 1
			else:
				prelim_trig_x = s_y_above.index(changed_state) - 1
		except ValueError:
			# error: no transition found
			return [None, 0]
		
		t, dydt = self.smp_to_time([sAOI[0] + prelim_trig_x])[0], 0
		if tau_samples > 2:
			tAOI_fit = self.smp_to_time([
				sAOI[0] + prelim_trig_x - tau_samples, 
				sAOI[0] + prelim_trig_x + tau_samples]
				)
			fitres = self.lin_fit(tAOI_fit)
			if fitres[2] == False:
				# error: fit failed
				print('Error in find_level_crossing(): fit failed.')
				return [None, 0]
			if abs(fitres[1]) < 1E-6:
				print('Warning: in find_level_crossing(): horizontal fit detected - refinement may be unstable.')
			# find intersection of fit line with trigger level 
			# by solving for t: level == fitres[0] + fitres[1] * t
			t_refined = (level - fitres[0])/fitres[1]
			dydt_refined = fitres[1]
			
			if abs(t_refined - t) < t_edge:
				# note: since tau_samples > 2, t_edge is already > 0
				# print('find_level_crossing: adjusting position by %g' % (t_refined - t))
				t = t_refined
				dydt = dydt_refined
			else:	
				print('Warning: in find_level_crossing(): refined value %g out of bounds: %g +/- %g. Defaulting to previous (integer) sample position.' % (t_refined, t, t_edge))

		# print('find_level_crossing result:', [t, dydt]) # DEBUG 
		return [t, dydt]
		

	def resampled_region(self, tAOI, nsmp):
		if nsmp <= 0:
			raise ValueError("nsmp = %d < 0" % nsmp)
			return []
		t_x  = np.linspace(start = tAOI[0], stop = tAOI[1] , num = nsmp, endpoint = False)
		s_x  = self.time_to_smp(t_x, force_inrange=True) 
		# list index out of range handling: repeat nearest neighbour			
		if s_x[-1] + 1 > len(self.s) - 2:
			s_x[-1] = s_x[-2] 
		# print(repr([s_x[0], s_x[1], s_x[-2], s_x[-1] ])) # DEBUG
		# create linear interpolated 1D data 
		r_re = [ 
			self.s[int(s_x[i])    ]*(1 - (s_x[i] - int(s_x[i]))) + 
			self.s[int(s_x[i]) + 1]*(    (s_x[i] - int(s_x[i]))) 
				for i in range(0, len(s_x)) ]
		return r_re
		

def arithmetic_operation(WFA_list, tAOI, func, generate_time_coords = False):
	# assume equidistant samples, find smallest timestep via list of AOI sample lengths
	n = [np.dot(wfa.time_to_smp(tAOI), [-1, 1]) + 1 for wfa in WFA_list]
	n_max = max(n)
	first_match_index = lambda list, value: next((idx for idx,val in enumerate(list) if val == value), 0) 
	idx_max = first_match_index(n, n_max)
	n_max = int(round(n_max)) # force integer to avoid float type aliasing / array length mismatch (+/-1 errors)	
	# prepare resampled data 
	rdata = np.array([wfa.resampled_region(tAOI, n_max) for wfa in WFA_list]).transpose()
	# feed list of individual samples to arithmetic function
	outp_t = []
	outp_y = list(map(func, rdata))	
	if generate_time_coords:
		outp_t = WFA_list[idx_max].samples_t(tAOI, n_max)
	return [outp_t, outp_y]
	
	
	