import numpy as np
from filterpy.kalman import KalmanFilter
import copy
class TrackBuffer():
	def __init__(self, info, ID, bbox3D, pcd, time_stamp, buffer_size): 
		self.id = ID
		self.info = info
		self.time_since_update = 0
		self.hits = 1  
  
		self.bbox = []
		self.NDT_voxels = []
		self.time_stamp = []
		self.kf_buffer = []
		self.match = True
		self.status = []
		self.buffer_size = buffer_size
		self.pcd_of_track = None
		self.KF_init(bbox3D)
		##UPDATE
		self.update_buffer(bbox3D,pcd,time_stamp)

	def get_velocity(self):
		# return the object velocity in the state
		return self.kf.x[7:]

	def update_buffer(self, bbox, voxel, time_stamp):
		self.bbox.append(bbox)
		self.NDT_voxels.append(voxel)
		self.time_stamp.append(time_stamp)
		self.kf_buffer.append(self.kf)
		self.match = True
  
	def KF_init(self, bbox3D):
		#Kalman filter
		self.kf = KalmanFilter(dim_x=10, dim_z=7)       
		# There is no need to use EKF here as the measurement and state are in the same space with linear relationship

		# state x dimension 10: x, y, z, theta, l, w, h, dx, dy, dz
		# constant velocity model: x' = x + dx, y' = y + dy, z' = z + dz 
		# while all others (theta, l, w, h, dx, dy, dz) remain the same
		self.kf.F = np.array([[1,0,0,0,0,0,0,1,0,0],      # state transition matrix, dim_x * dim_x
							  [0,1,0,0,0,0,0,0,1,0],
							  [0,0,1,0,0,0,0,0,0,1],
							  [0,0,0,1,0,0,0,0,0,0],  
							  [0,0,0,0,1,0,0,0,0,0],
							  [0,0,0,0,0,1,0,0,0,0],
							  [0,0,0,0,0,0,1,0,0,0],
							  [0,0,0,0,0,0,0,1,0,0],
							  [0,0,0,0,0,0,0,0,1,0],
							  [0,0,0,0,0,0,0,0,0,1]])     

		# measurement function, dim_z * dim_x, the first 7 dimensions of the measurement correspond to the state
		self.kf.H = np.array([[1,0,0,0,0,0,0,0,0,0],      
							  [0,1,0,0,0,0,0,0,0,0],
							  [0,0,1,0,0,0,0,0,0,0],
							  [0,0,0,1,0,0,0,0,0,0],
							  [0,0,0,0,1,0,0,0,0,0],
							  [0,0,0,0,0,1,0,0,0,0],
							  [0,0,0,0,0,0,1,0,0,0]])

		# measurement uncertainty, uncomment if not super trust the measurement data due to detection noise
		# self.kf.R[0:,0:] *= 10.   

		# initial state uncertainty at time 0
		# Given a single data, the initial velocity is very uncertain, so giv a high uncertainty to start
		self.kf.P[7:, 7:] *= 1000. 	
		self.kf.P *= 10.

		# process uncertainty, make the constant velocity part more certain
		self.kf.Q[7:, 7:] *= 0.01

		# initialize data
		self.kf.x[:7] = bbox3D.reshape((7, 1))
  
def KF_predict(kf,time=1):
	""" predict the state of the kalman filter
	"""
	new_kf = copy.copy(kf)
	for t in range(time):
		new_kf.predict()
	new_kf.predict()
	return new_kf
		
		