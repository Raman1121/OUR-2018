import keras.backend as K
import tensorflow as tf
from keras import initializers, layers
import numpy as np
from sklearn.metrics import confusion_matrix
import pandas as pd
from sklearn import preprocessing


class Length(layers.Layer):
	"""
	Compute the length of vectors. This is used to compute a Tensor that has the same shape with y_true in margin_loss
	inputs: shape=[dim_1, ..., dim_{n-1}, dim_n]
	output: shape=[dim_1, ..., dim_{n-1}]
	"""
	def call(self, inputs, **kwargs):
		return K.sqrt(K.sum(K.square(inputs), -1))

	def compute_output_shape(self, input_shape):
		return input_shape[:-1]

class Mask(layers.Layer):
	"""
	Mask a Tensor with shape=[None, d1, d2] by the max value in axis=1.
	Output shape: [None, d2]
	"""
	def call(self, inputs, **kwargs):
		# use true label to select target capsule, shape=[batch_size, num_capsule]
		if type(inputs) is list:  # true label is provided with shape = [batch_size, n_classes], i.e. one-hot code.
			assert len(inputs) == 2
			inputs, mask = inputs
		else:  # if no true label, mask by the max length of vectors of capsules
			x = inputs
			# Enlarge the range of values in x to make max(new_x)=1 and others < 0
			x = (x - K.max(x, 1, True)) / K.epsilon() + 1
			mask = K.clip(x, 0, 1)  # the max value in x clipped to 1 and other to 0

		# masked inputs, shape = [batch_size, dim_vector]
		inputs_masked = K.batch_dot(inputs, mask, [1, 1])
		return inputs_masked

	def compute_output_shape(self, input_shape):
		if type(input_shape[0]) is tuple:  # true label provided
			return tuple([None, input_shape[0][-1]])
		else:
			return tuple([None, input_shape[-1]])


def squash(vectors, axis=-1):
	"""
	The non-linear activation used in Capsule. It drives the length of a large vector to near 1 and small vector to 0
	:param vectors: some vectors to be squashed, N-dim tensor
	:param axis: the axis to squash
	:return: a Tensor with same shape as input vectors
	"""
	s_squared_norm = K.sum(K.square(vectors), axis, keepdims=True)
	scale = s_squared_norm / (1 + s_squared_norm) / K.sqrt(s_squared_norm)
	return scale * vectors


class CapsuleLayer(layers.Layer):
	"""
	The capsule layer. It is similar to Dense layer. Dense layer has `in_num` inputs, each is a scalar, the output of the 
	neuron from the former layer, and it has `out_num` output neurons. CapsuleLayer just expand the output of the neuron
	from scalar to vector. So its input shape = [None, input_num_capsule, input_dim_vector] and output shape = \
	[None, num_capsule, dim_vector]. For Dense Layer, input_dim_vector = dim_vector = 1.
	
	:param num_capsule: number of capsules in this layer
	:param dim_vector: dimension of the output vectors of the capsules in this layer
	:param num_routings: number of iterations for the routing algorithm
	"""
	def __init__(self, num_capsule, dim_vector, num_routing=3,
				 kernel_initializer='glorot_uniform',
				 bias_initializer='zeros',
				 **kwargs):
		super(CapsuleLayer, self).__init__(**kwargs)
		self.num_capsule = num_capsule
		self.dim_vector = dim_vector
		self.num_routing = num_routing
		self.kernel_initializer = initializers.get(kernel_initializer)
		self.bias_initializer = initializers.get(bias_initializer)

	def build(self, input_shape):
		assert len(input_shape) >= 3, "The input Tensor should have shape=[None, input_num_capsule, input_dim_vector]"
		self.input_num_capsule = input_shape[1]
		self.input_dim_vector = input_shape[2]

		# Transform matrix
		self.W = self.add_weight(shape=[self.input_num_capsule, self.num_capsule, self.input_dim_vector, self.dim_vector],
								 initializer=self.kernel_initializer,
								 name='W')

		# Coupling coefficient. The redundant dimensions are just to facilitate subsequent matrix calculation.
		self.bias = self.add_weight(shape=[1, self.input_num_capsule, self.num_capsule, 1, 1],
									initializer=self.bias_initializer,
									name='bias',
									trainable=False)
		self.built = True

	def call(self, inputs, training=None):
		# inputs.shape=[None, input_num_capsule, input_dim_vector]
		# Expand dims to [None, input_num_capsule, 1, 1, input_dim_vector]
		inputs_expand = K.expand_dims(K.expand_dims(inputs, 2), 2)

		# Replicate num_capsule dimension to prepare being multiplied by W
		# Now it has shape = [None, input_num_capsule, num_capsule, 1, input_dim_vector]
		inputs_tiled = K.tile(inputs_expand, [1, 1, self.num_capsule, 1, 1])

		"""  
		# Compute `inputs * W` by expanding the first dim of W. More time-consuming and need batch_size.
		# Now W has shape  = [batch_size, input_num_capsule, num_capsule, input_dim_vector, dim_vector]
		w_tiled = K.tile(K.expand_dims(self.W, 0), [self.batch_size, 1, 1, 1, 1])
		
		# Transformed vectors, inputs_hat.shape = [None, input_num_capsule, num_capsule, 1, dim_vector]
		inputs_hat = K.batch_dot(inputs_tiled, w_tiled, [4, 3])
		"""
		# Compute `inputs * W` by scanning inputs_tiled on dimension 0. This is faster but requires Tensorflow.
		# inputs_hat.shape = [None, input_num_capsule, num_capsule, 1, dim_vector]
		inputs_hat = tf.scan(lambda ac, x: K.batch_dot(x, self.W, [3, 2]),
							 elems=inputs_tiled,
							 initializer=K.zeros([self.input_num_capsule, self.num_capsule, 1, self.dim_vector]))
		"""
		# Routing algorithm V1. Use tf.while_loop in a dynamic way.
		def body(i, b, outputs):
			c = tf.nn.softmax(self.bias, dim=2)  # dim=2 is the num_capsule dimension
			outputs = squash(K.sum(c * inputs_hat, 1, keepdims=True))
			b = b + K.sum(inputs_hat * outputs, -1, keepdims=True)
			return [i-1, b, outputs]

		cond = lambda i, b, inputs_hat: i > 0
		loop_vars = [K.constant(self.num_routing), self.bias, K.sum(inputs_hat, 1, keepdims=True)]
		_, _, outputs = tf.while_loop(cond, body, loop_vars)
		"""
		# Routing algorithm V2. Use iteration. V2 and V1 both work without much difference on performance
		assert self.num_routing > 0, 'The num_routing should be > 0.'
		for i in range(self.num_routing):
			c = tf.nn.softmax(self.bias, dim=2)  # dim=2 is the num_capsule dimension
			# outputs.shape=[None, 1, num_capsule, 1, dim_vector]
			outputs = squash(K.sum(c * inputs_hat, 1, keepdims=True))

			# last iteration needs not compute bias which will not be passed to the graph any more anyway.
			if i != self.num_routing - 1:
				# self.bias = K.update_add(self.bias, K.sum(inputs_hat * outputs, [0, -1], keepdims=True))
				self.bias += K.sum(inputs_hat * outputs, -1, keepdims=True)
			# tf.summary.histogram('BigBee', self.bias)  # for debugging
		return K.reshape(outputs, [-1, self.num_capsule, self.dim_vector])

	def compute_output_shape(self, input_shape):
		return tuple([None, self.num_capsule, self.dim_vector])


def PrimaryCap(inputs, dim_vector, n_channels, kernel_size, strides, padding):
	"""
	Apply Conv1D `n_channels` times and concatenate all capsules
	:param inputs: 4D tensor, shape=[None, width, height, channels]
	:param dim_vector: the dim of the output vector of capsule
	:param n_channels: the number of types of capsules
	:return: output tensor, shape=[None, num_capsule, dim_vector]
	"""
	output = layers.Conv1D(filters=dim_vector*n_channels, kernel_size=kernel_size, strides=strides, padding=padding)(inputs)
	outputs = layers.Reshape(target_shape=[-1, dim_vector])(output)
	return layers.Lambda(squash)(outputs)


# BUILDING THE MODEL

from keras import layers, models
from keras import backend as K
from keras.utils import to_categorical
from keras import callbacks

def CapsNet(input_shape, n_class, num_routing):
	"""
	A Capsule Network on MNIST.
	:param input_shape: data shape, 4d, [None, width, height, channels]
	:param n_class: number of classes
	:param num_routing: number of routing iterations
	:return: A Keras Model with 2 inputs and 2 outputs
	"""
	x = layers.Input(shape=input_shape)
	print(input_shape, x.shape)

	# Layer 1: Just a conventional Conv1D layer
	conv1 = layers.Conv1D(filters=256, kernel_size=9, strides=1, padding='valid', activation='relu', name='conv1')(x)

	# Layer 2: Conv1D layer with `squash` activation, then reshape to [None, num_capsule, dim_vector]
	primarycaps = PrimaryCap(conv1, dim_vector=8, n_channels=32, kernel_size=9, strides=2, padding='valid')

	# Layer 3: Capsule layer. Routing algorithm works here.
	digitcaps = CapsuleLayer(num_capsule=n_class, dim_vector=16, num_routing=num_routing, name='digitcaps')(primarycaps)

	# Layer 4: This is an auxiliary layer to replace each capsule with its length. Just to match the true label's shape.
	# If using tensorflow, this will not be necessary. :)
	out_caps = Length(name='out_caps')(digitcaps)

	# Decoder network.
	y = layers.Input(shape=(n_class,))
	masked = Mask()([digitcaps, y])  # The true label is used to mask the output of capsule layer.
	x_recon = layers.Dense(512, activation='relu')(masked)
	x_recon = layers.Dense(1024, activation='relu')(x_recon)
	x_recon = layers.Dense(247, activation='sigmoid')(x_recon)
	x_recon = layers.Reshape(target_shape=[247, 1], name='out_recon')(x_recon)

	# two-input-two-output keras Model
	return models.Model([x, y], [out_caps, x_recon])


## Defining the Loss Function

def margin_loss(y_true, y_pred):
	"""
	Margin loss for Eq.(4). When y_true[i, :] contains not just one `1`, this loss should work too. Not test it.
	:param y_true: [None, n_classes]
	:param y_pred: [None, num_capsule]
	:return: a scalar loss value.
	"""
	L = y_true * K.square(K.maximum(0., 0.9 - y_pred)) + \
		0.5 * (1 - y_true) * K.square(K.maximum(0., y_pred - 0.1))

	return K.mean(K.sum(L, 1))


def train(model, data, epoch_size_frac=1.0):
	"""
	Training a CapsuleNet
	:param model: the CapsuleNet model
	:param data: a tuple containing training and testing data, like `((x_train, y_train), (x_test, y_test))`
	:param args: arguments
	:return: The trained model
	"""
	# unpacking the data
	(x_train, y_train), (x_test, y_test) = data
	
	global y_pred

	# callbacks
	log = callbacks.CSVLogger('log.csv')
	checkpoint = callbacks.ModelCheckpoint('weights-{epoch:02d}.h5',
										   save_best_only=True, save_weights_only=True, verbose=1)
	lr_decay = callbacks.LearningRateScheduler(schedule=lambda epoch: 0.001 * np.exp(-epoch / 10.))

	# compile the model
	model.compile(optimizer='adam',
				  loss=[margin_loss, 'mse'],
				  loss_weights=[1., 0.0005],
				  metrics={'out_caps': 'accuracy'})
	
	
	model.fit([x_train, y_train], [y_train, x_train], batch_size=32, epochs=50,
			  validation_data=[[x_test, y_test], [y_test, x_test]])
	
	model.save_weights('trained_model.h5')
	print('Trained model saved to \'trained_model.h5\'')
	
	return model


if __name__ == "__main__":

	from imblearn.over_sampling import SMOTE
	sm = SMOTE(random_state=2)

	model = CapsNet(input_shape=[ 247, 1],
			n_class=2,
			num_routing=3)

	model.summary()

	#Load the data
	filename = '/home/raman/Desktop/Test OUR/CDK2_Final_Combined.csv'
	df4 = pd.read_csv(filename)

	#Normalizing the data
	
	from sklearn import preprocessing
	x = df4.values #returns a numpy array
	min_max_scaler = preprocessing.MinMaxScaler()
	x_scaled = min_max_scaler.fit_transform(x)
	df4 = pd.DataFrame(x_scaled)


	X_full_new = df4.iloc[:,1:248].values
	y_full_new = df4.iloc[:,248].values

	X_full_new2, y_full_new2= sm.fit_sample(X_full_new, y_full_new.ravel())

	from sklearn.model_selection import train_test_split
	x_train, x_test, y_train, y_test = train_test_split(X_full_new2, y_full_new2, test_size = 0.3, random_state = 42)

	#x_train.shape, x_test.shape, y_train.shape, y_test.shape

	#Print these shapes here
	#x_train.shape, x_test.shape, y_train.shape, y_test.shape


	#Reshaping the feature samples
	x_train_reshape = x_train.reshape(347548, 247, 1)
	y_train_reshape = y_train.reshape(347548, 1)
	x_test_reshape = x_test.reshape(148950, 247, 1)
	y_test_reshape = y_test.reshape(148950, 1)

	#Reshaping the labels
	y_train_ = tf.keras.utils.to_categorical(y_train_reshape,num_classes=2)
	y_test_ = tf.keras.utils.to_categorical(y_test_reshape[:100],num_classes=2)

	train(model=model, data=((x_train_reshape, y_train_), (x_test_reshape[:100], y_test_)), epoch_size_frac = 0.5)





