var inputTypes = 'Web Links';
var outputTypes = 'Web Links';

var externalLinkField = "external.ExternalLinkTo_-98R4a_4EeekDP1y4xXYPQ";

function transform(context, input) {
    // input appears to be an ARRAY!
    console.log("targetRepositoryArtifact: " + JSON.stringify(context.targetRepositoryArtifact))
    console.log("INPUT:: " + JSON.stringify(input))
    var links = context.targetRepositoryArtifact[externalLinkField]
    console.log("CURRENT LINKS: "+JSON.stringify(links))

    // Iterate over links
    for (i = 0; i < links.length; i++) {
        // Match Location
        if (links[i].location === input[0].location)
        // Match label
            if (links[i].label === input[0].label) {
                console.log("Found identical link: " + JSON.stringify(input))
                return links
            }
            else {
                // Update Label
                links = links.splice(i, 1, input[0])
                console.log("Modified existing link: " + JSON.stringify(links))
                return links
            }
        else {
            // Add New Link
            links = links.concat(input).sort(function (a, b) {
                return a.label.localeCompare(b.label);
            });
            console.log("Added new link: " + JSON.stringify(links))
            return links
        }
    }
}