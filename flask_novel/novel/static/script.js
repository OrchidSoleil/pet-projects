function sendChoiceOutcomeToServer(choiceOutcome) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/game', false);
    xhr.setRequestHeader('Content-Type', 'application/json');

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                const contentType = xhr.getResponseHeader('Content-Type');
                if (contentType && contentType.indexOf('application/json') !== -1) {
                    // Handle JSON response
                    const responseData = JSON.parse(xhr.responseText);
                    updateHTML(responseData);
                } else if (contentType && contentType.indexOf('text/html') !== -1) {
                    // Handle HTML response
                    document.documentElement.innerHTML = xhr.responseText;
                } else {
                    // Handle other response types or errors
                }
            } else {
                // Handle error cases
            }
        }
    };


    const data = JSON.stringify({ choiceOutcome });
    xhr.send(data);
}


function updateHTML(data) {
    document.querySelector('#story').textContent = data.story_text;
    document.querySelector('img.main').src = data.img_path;
    document.getElementById('location').textContent = `${data.location}, ${data.chapter}`;
    //document.getElementById('chapter').textContent = data.chapter;

    // update choices and outcomes
    const choices = document.querySelectorAll('.choice');
    var index = 0
        
    for (const newChoice in data.choices) {
        choices[index].textContent = newChoice
        const newOutcome = data.choices[newChoice];
        choices[index].setAttribute('choice-outcome', newOutcome);
        index++
        };

    // if there's only one choice for particular story, clear text of other previous choices
    if (index == 1) {
        choices[index].textContent = ""
    }
};

const choices = document.querySelectorAll('.choice'); 
choices.forEach(choice => {
    choice.addEventListener('click', getOutcome);
});

function getOutcome(event) {
    const clickedChoice = event.target;
    const choiceOutcome = clickedChoice.getAttribute('choice-outcome');
    sendChoiceOutcomeToServer(choiceOutcome);
};