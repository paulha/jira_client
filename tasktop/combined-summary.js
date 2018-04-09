var inputTypes = ['String', 'String']
var outputTypes = 'String'

function transform(context, input) {
	return '(' + input[0] + ') ' + input[1]
}
