from djitellopy import Tello
import cv2
import pygame
from pygame.locals import *
import numpy as np
import time
import sys
import os
import matplotlib.pyplot as plt

# #todo: readme for project

# FPS = 25	# 1/FPS seconds = time program pauses between frames
# markerLength = 9.4 # 2 cm = phone; 10 cm = printout


# #aruco dictionary
# aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_1000) #markers w/ id 1-1000 may be used
# arucoParams = cv2.aruco.DetectorParameters_create()

# #calibration setup
# calibrationFile = "calibrationFileName.xml"
# calibrationParams = cv2.FileStorage(calibrationFile, cv2.FILE_STORAGE_READ)
# camera_matrix = calibrationParams.getNode("cameraMatrix").mat()
# dist_coeffs = calibrationParams.getNode("distCoeffs").mat()
# r = calibrationParams.getNode("R").mat()
# new_camera_matrix = calibrationParams.getNode("newCameraMatrix").mat()

# #facial detection setup
# face_cascade = cv2.CascadeClassifier('Haarcascades/haarcascade_frontalface_default.xml')
# eye_cascade = cv2.CascadeClassifier('Haarcascades/haarcascade_eye.xml')


# def cameraPoseFromHomography(H):
# 	H1 = H[:, 0]
# 	H2 = H[:, 1]
# 	H3 = np.cross(H1, H2)

# 	norm1 = np.linalg.norm(H1)
# 	norm2 = np.linalg.norm(H2)
# 	tnorm = (norm1 + norm2) / 2.0

# 	T = H[:, 2] / tnorm
# 	return np.mat([H1, H2, H3, T])

# def draw(img, corners, imgpts):
	# imgpts = np.int32(imgpts).reshape(-1, 2)

	# # draw ground floor in green
	# img = cv2.drawContours(img, [imgpts[:4]], -1, (0, 255, 0), -3)

	# # draw pillars in blue color
	# for i, j in zip(range(4), range(4, 8)):
	# 	img = cv2.line(img, tuple(imgpts[i]), tuple(imgpts[j]), (255), 3)

	# # draw top layer in red color
	# img = cv2.drawContours(img, [imgpts[4:]], -1, (0, 0, 255), 3)
	# return img


class FrontEnd(object):
	""" Maintains the Tello display and moves it through the keyboard keys.
		Press escape key to quit.
		The controls are:
			- T: Takeoff
			- L: Land
			- Arrow keys: Forward, backward, left and right.
			- A and D: Counter clockwise and clockwise rotations
			- W and S: Up and down.
	"""

	def __init__(self, tello, land):
		self.tello = tello
		self.land = land
		# Init pygame
		pygame.init()

		# Creat pygame window
		pygame.display.set_caption("Tello Landing Stream")
		self.screen = pygame.display.set_mode([400,300]) # ((width, height) of window))

		# Init Tello object that interacts with the Tello drone
		# self.tello = Tello()
		# self.tello.connect()

		# Check if battery level stable
		# batt=self.tello.get_battery()
		# if int(batt)<20: 
		# 	print (" no battery", batt)
		# 	sys.exit(0)
		# print(batt)
		# self.tello.get_frame_read()

		# Drone velocities between -100~100
		self.for_back_velocity = 0
		self.left_right_velocity = 0
		self.up_down_velocity = 0
		self.yaw_velocity = 0
		self.speed = 10

		# create update timer
		pygame.time.set_timer(USEREVENT + 1, 100)


	def run(self):
		FPS = 25	# 1/FPS seconds = time program pauses between frames
		markerLength = 9.4 # 2 cm = phone; 10 cm = printout


		#aruco dictionary
		aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_1000) #markers w/ id 1-1000 may be used
		arucoParams = cv2.aruco.DetectorParameters_create()

		#calibration setup
		calibrationFile = "calibrationFileName.xml"
		calibrationParams = cv2.FileStorage(calibrationFile, cv2.FILE_STORAGE_READ)
		camera_matrix = calibrationParams.getNode("cameraMatrix").mat()
		dist_coeffs = calibrationParams.getNode("distCoeffs").mat()
		# r = calibrationParams.getNode("R").mat()
		# new_camera_matrix = calibrationParams.getNode("newCameraMatrix").mat()	

		# if not self.tello.connect():
		# 	print("Tello not connected")
			# return
		# if not self.tello.set_speed(self.speed):
		# 	print("Not set speed to lowest possible")
		# 	self.speed = 10
			# return
		# if not self.tello.streamoff():# In case streaming is on. This happens when we quit this program without the escape key.
		# 	print("Could not stop video stream")
		# 	return
		# if not self.tello.streamon():
		# 	print("Could not start video stream")
		# 	return
		self.tello.set_speed(self.speed)
		# self.tello.send_command_with_return("downvision 0")
		# frame_read = self.tello.get_frame_read()
		
		# time.sleep(0.1)
		self.tello.send_command_with_return("downvision 1")
		frame_read = self.tello.get_frame_read()
		print(frame_read.frame)
		time.sleep(0.1)
		kp_xyz = [.15,.3,.4]	#proportional constants
		ki_xyz = [0,0.05,0]		#integral constants
		kd_xyz = [.05,.1,.1]	#derivative constants

		desired_xyz = [0,0,40]	#desired xyz distance from aruco
		if self.land==True:
			land_xyz = [10,10,20] 		#range needed within desired to cut motors + attempt landing
		else:
			land_xyz = [5,5,20]

		bias_xyz = [0,0,0]
		integral_xyz = [0,0,0]
		prev_error_xyz = [0,0,0]
		error_xyz = [0,0,0]

		# plt.ion() #interactive mode on
		# t = 0;	#time (used for plotting)
		# plt.pause(0.001)
		# t = t + 0.001
		land_count= 0

		self.send_rc_control = True
		should_stop = False
		while not should_stop:

			for event in pygame.event.get():
				# if event.type == USEREVENT + 1:
				# 	self.update()
				if event.type == QUIT:
					pygame.display.quit()
					pygame.quit()
					should_stop = True
				elif event.type == KEYDOWN:
					if event.key == K_ESCAPE:
						pygame.display.quit()
						pygame.quit()
						should_stop = True
					else:
						self.keydown(event.key)
				elif event.type == KEYUP:
					self.keyup(event.key)

			if frame_read.stopped:
				frame_read.stop()
				break

			self.screen.fill([0, 0, 0])

			frame = frame_read.frame
			img = cv2.rotate(frame,cv2.ROTATE_90_CLOCKWISE)
			gray = img
			size = img.shape


			avg1 = np.float32(gray)
			avg2 = np.float32(gray)
			res = cv2.aruco.detectMarkers(gray, aruco_dict, parameters = arucoParams)
			imgWithAruco = img # assign imRemapped_color to imgWithAruco directly
			# if len(res[0]) > 0:
			# 	print (res[0])


			focal_length = size[1]
			center = (size[1]/2, size[0]/2)
			camera_matrix = np.array(
							[[focal_length, 0, center[0]],
							[0, focal_length, center[1]],
							[0, 0, 1]], dtype = "double"
							)

			if res[1] != None: # if aruco marker detected
				im_src = imgWithAruco
				im_dst = imgWithAruco

				pts_dst = np.array([[res[0][0][0][0][0], res[0][0][0][0][1]], [res[0][0][0][1][0], res[0][0][0][1][1]], [res[0][0][0][2][0], res[0][0][0][2][1]], [res[0][0][0][3][0], res[0][0][0][3][1]]])
				pts_src = pts_dst
				h, status = cv2.findHomography(pts_src, pts_dst)

				imgWithAruco = cv2.warpPerspective(im_src, h, (im_dst.shape[1], im_dst.shape[0]))

				rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(res[0], markerLength, camera_matrix, dist_coeffs)
				img = cv2.aruco.drawAxis(imgWithAruco, camera_matrix, dist_coeffs, rvec, tvec, 10)
				# cameraPose = cameraPoseFromHomography(h)

				#PID controller

				xyz = []
				xyz.append(tvec[0][0][0])
				xyz.append(tvec[0][0][1])
				xyz.append(tvec[0][0][2])

				# plt.subplot(311)
				# plt.plot(t, xyz[0], 'rs')
				# plt.subplot(312)
				# plt.plot(t, xyz[1], 'gs')
				# plt.subplot(313)
				# plt.plot(t, xyz[2], 'bs')

				iteration_time = 1/FPS

				error_xyz = []
				derivative_xyz = []
				output_xyz = []
				final_output_xyz=[0,0,0]
				for i in range(2):
					error_xyz.append(desired_xyz[i] - xyz[i])
					integral_xyz[i] = integral_xyz[i] + (error_xyz[i] * iteration_time)
					derivative_xyz.append(error_xyz[i] - prev_error_xyz[i])
					output_xyz.append(kp_xyz[i]*error_xyz[i] + ki_xyz[i]*integral_xyz[i] + kd_xyz[i]*derivative_xyz[i] + bias_xyz[i])
					prev_error_xyz[i] = error_xyz[i]

					#speed can only be 10-100, if outside of range, set to 10 or 100
					# print(output_xyz)
					if output_xyz[i] > 10:
						output_xyz[i] = 7
					elif output_xyz[i] < -10:
						output_xyz[i] = -10
					elif output_xyz[i] > 0 and output_xyz[i] < 5 :
						output_xyz[i] = 5
					elif output_xyz[i] < 0 and output_xyz[i] > -5 :
						output_xyz[i] = -5
					# if xyz[i] <-5 :
					# 	final_output_xyz[i] = 10
					# elif xyz[i] > 5:
					# 	final_output_xyz[i] = -10

				error_xyz.append(desired_xyz[2] - xyz[2])
				integral_xyz[2] = integral_xyz[2] + (error_xyz[2] * iteration_time)
				derivative_xyz.append(error_xyz[2] - prev_error_xyz[2])
				output_xyz.append(kp_xyz[2]*error_xyz[2] + ki_xyz[2]*integral_xyz[2] + kd_xyz[2]*derivative_xyz[2] + bias_xyz[2])
				prev_error_xyz[2] = error_xyz[2]			
				if output_xyz[2] < -10:
					output_xyz[2]=-10	


				self.for_back_velocity = int(output_xyz[1])
				# if output_xyz[1]>10 or output_xyz[1]<-10:
				# 	self.yaw_velocity = int(output_xyz[1])

				# self.up_down_velocity = int(final_output_xyz[2])
				self.left_right_velocity = int(-output_xyz[0])
				# print('leftright',self.left_right_velocity,'farback', self.for_back_velocity, self.up_down_velocity,self.yaw_velocity)
				# if xyz[0] < desired_xyz[0] + land_xyz[0] and xyz[0] > desired_xyz[0] - land_xyz[0] and xyz[1] < desired_xyz[1] + land_xyz[1] and xyz[1] >desired_xyz[1] - land_xyz[1] and xyz[2] < desired_xyz[2] + land_xyz[2] and xyz[2] > desired_xyz[2] - land_xyz[2]:
				if xyz[0] < desired_xyz[0] + land_xyz[0] and xyz[0] > desired_xyz[0] - land_xyz[0] and xyz[1] < desired_xyz[1] + land_xyz[1] and xyz[1] >desired_xyz[1] - land_xyz[1]:
					
					# self.left_right_velocity, self.for_back_velocity = -self.left_right_velocity, -self.for_back_velocity
					# self.update()
					self.left_right_velocity, self.for_back_velocity = 0,0
					# self.tello.send_command_with_return("stop")
					self.update()
					# time.sleep(1)
					print("adjusting z axis")
					self.up_down_velocity = int(output_xyz[2])
					self.update()

					if self.land == True:
						if xyz[2] < 60:
							self.up_down_velocity = 0
							self.update()
							land_count+=1
							print("within range, ",land_count)
							
							if land_count > 3:
								self.send_rc_control = False
								print('land now!!!')
								self.tello.land()
								time.sleep(0.5)
								pygame.display.quit()
								pygame.quit()
								return
							# cv2.destroyAllWindows()

					elif self.land == False:
						if xyz[2] < 100 :
							self.up_down_velocity = 0
							land_count+=1
							print("within range, ready to fly ",land_count)
							
							if land_count > 3:
								self.send_rc_control = False
								print('FLY now!!!')
								pygame.display.quit()
								pygame.quit()
								return
				else:
					if land_count>2:
						land_count=-1
				
				print("off_x: -", xyz[0], self.left_right_velocity,"off_y:", xyz[1], self.for_back_velocity, "off_z:", xyz[2], self.for_back_velocity, sep="\t")


				#consider using gain scheduling (different constants at different distances)
			elif self.land==True:
				self.left_right_velocity, self.for_back_velocity, self.up_down_velocity,self.yaw_velocity = 0,0,0,0
			

			self.update()

			img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
			frame = np.rot90(img)
			frame = np.flipud(frame)
			frame = pygame.surfarray.make_surface(frame)

			self.screen.blit(frame, (0, 0))
			pygame.display.update()

			#xyz graphing
			# plt.show()
			# plt.pause(1 / FPS)
			# t = t + 1/FPS

		#deallocate resources.
		# self.tello.end()
		# cv2.destroyAllWindows()

	def keydown(self, key):
		""" Update velocities based on key pressed
		Arguments:
			key: pygame key
		"""



	def keyup(self, key):
		""" Update velocities based on key released
		Arguments:
			key: pygame key
		"""

		if key == pygame.K_t:  # takeoff
			self.tello.takeoff()
			self.send_rc_control = True
		elif key == pygame.K_l:  # land
			self.tello.land()
			self.send_rc_control = True
		elif key == pygame.K_e:		#release E to turn off all motors (for our automated landing)
			self.tello.emergency()
			self.send_rc_control = False
			
		elif key == pygame.K_z:		#release E to turn off all motors (for our automated landing)
			self.tello.send_command_with_return('downvision 0')
			frame_read = self.tello.get_frame_read()
			self.send_rc_control = True

		elif key == pygame.K_x:		#release E to turn off all motors (for our automated landing)
			self.tello.send_command_with_return('downvision 1')
			frame_read = self.tello.get_frame_read()
			self.send_rc_control = True

	def update(self):
		""" Update routine. Send velocities to Tello."""
		if self.send_rc_control:
			self.tello.send_rc_control(self.left_right_velocity, self.for_back_velocity, self.up_down_velocity,
									self.yaw_velocity)


def main():
	frontend = FrontEnd()

	# run frontend
	frontend.run()


if __name__ == '__main__':
	main()
