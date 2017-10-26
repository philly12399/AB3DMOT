% Author: Xinshuo
% Email: xinshuow@andrew.cmu.edu

% this function takes a line segment in and output the line in 2d space
% parameters
%	segment:		1 x 4 or more
%
% output
%	line:	1 x 3 vector [a, b, c] -> represent ax + by + c = 0

function line_2d = get_2dline_from_segment(line_segment, debug_mode)
	if nargin < 2
		debug_mode = true;
	end

	if debug_mode
		assert(size(line_segment, 1) == 1 && size(line_segment, 2) >= 4, 'the size of input line segment is not correct');
	end

	pts1 = line_segment(1, 1:2);
	pts2 = line_segment(1, 3:4);

	line_2d = get_2dline_from_pts(pts1, pts2, debug_mode);
end