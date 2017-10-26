% Author: Xinshuo Weng
% Email: xinshuow@andrew.cmu.edu


% given the state of hidden variable and current weights of RBM, inferring the probability of visible variable
function post_activation = forward_hidden_rbm(rbm_weight, var_hidden, debug_mode)
	if nargin < 3
		debug_mode = true;
	end

	if debug_mode
		assert(isstruct(rbm_weight), 'the weight should be a struct \n');
		assert(isfield(rbm_weight, 'W'), 'the weights in RBM do not exist');
		assert(isfield(rbm_weight, 'bias_visible'), 'the bias of visible variable in RBM do not exist');
	end

	% W, b are cells of matrix to store the weight and bias
	W = rbm_weight.W;				% num_hidden x num_visible
	bias_visible = rbm_weight.bias_visible;

	if debug_mode
		assert(size(W, 2) == size(bias_visible, 1), sprintf('the input number of neurons should be equal in weight and bias: %d vs %d\n', size(W, 1), size(bias_visible, 1)));
		assert(1 == size(bias_visible, 2), 'the second dimension of bias in visible variable should be equal 1\n');
		assert(all(size(var_hidden) == [size(W, 1), 1]), 'The shape of input hidden variable is not correct\n');
	end

	pre_activation = bias_visible + W' * var_hidden;		% num_visible x 1
	post_activation = mysigmoid(pre_activation);
end
