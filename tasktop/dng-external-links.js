var inputTypes = ['Location', 'String']
var outputTypes = 'Web Links'

var externalLinkField = "external.ExternalLinkTo_Pb21sNNWEeazFuziWsbfBA"

/**
 * This file has limitations:
 *
 * 		* It doesn't handle more than one link
 * 		* It won't handle changes in the label (platform name)
 *
 * @param context
 * @param input
 * @returns {*}
 */

function transform(context, input) {
	console.log("targetRepositoryArtifact: " + JSON.stringify(context.targetRepositoryArtifact))
	var newLink = {
		label:input[1],
		location:input[0]
	}
	var links = context.targetRepositoryArtifact[externalLinkField]
	if(links.some(hasLocation, newLink)) return links
	links.push(newLink)
	return links
}

function hasLocation(currentLink){
	return currentLink.location === this.location
}