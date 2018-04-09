var inputTypes = 'Web Links';
var outputTypes = 'Web Links';

var externalLinkField = "external.ExternalLinkTo_-98R4a_4EeekDP1y4xXYPQ";

var NOT_FOUND = -1;

function transform(context, input) {
    // Input is an ARRAY of length 1!
    console.log("targetRepositoryArtifact: " + JSON.stringify(context.targetRepositoryArtifact));
    console.log("INPUT:: " + JSON.stringify(input));
    var links = context.targetRepositoryArtifact[externalLinkField];
    var item = input[0];
    console.log("CURRENT LINKS: " + JSON.stringify(links));

    // Find by location:
    var pos = NOT_FOUND;
    for (var i = 0; i < links.length; i++) {
        if (links[i].location === item.location) {
            pos = i;
            break
        }
    }

    if (pos===NOT_FOUND) {
        // Wasn't found, add to array
        console.log("Added a link: " + JSON.stringify(item));
        links.push(item)
    }
    else {
        // Has the label changed?
        if (links[pos].label===item.label) {
            // No, just return the item
            console.log("Link exists: " + JSON.stringify(links));
            return links
        }
        else {
            // Yes, update, then sort below
            console.log("Update link label: " + JSON.stringify(item));
            links[pos].label = item.label
        }
    }

    // Sort: new item added or label was changed:
    links = links.sort(function (a, b) {
        return a.label.localeCompare(b.label);
    });

    console.log("Sorted links: " + JSON.stringify(links));
    return links
}