document.addEventListener('DOMContentLoaded', function() {
    // add event listener to switch to edit view on button click
    let edit_buttons = document.querySelectorAll('.edit-post-button');
    edit_buttons.forEach(button => {
        button.addEventListener('click', edit_mode);
        });
    // add event listener to like posts
    let like_buttons = document.querySelectorAll('.likes');
    like_buttons.forEach(button => {
        button.addEventListener('click', like_unlike);
    });
    //only add eventListener to a follow button on the pages where it exists
    let followButton = document.querySelector('#following');
    if (followButton !== null) {
    followButton.addEventListener('click', follow);
    }

});

function edit_mode(event) {

    // change button name to 'Save' in edit mode and assing id
    this.innerText = "Save";
    this.id = 'saving-changes';
    // change Edit button functionality to Save
    this.addEventListener('click', saving_changes);
    this.removeEventListener('click', edit_mode);

    // find the div, where the button is and in it find div to hide, this way button shouldn't be inside div to hide it
    let parentDiv = this.closest('.single-post');
    let postText = parentDiv.querySelector('.post-text');

    // hide the div with post text and substitue it with textarea from django form
    postText.style.display = 'none';
    let editForm = parentDiv.querySelector('.edit-post-field');
    editForm.style.display = 'block';
    // populate textarea with existing comment text
    let textarea = parentDiv.querySelector('textarea');
    textarea.value = postText.innerText;
    // adding id to textarea to later find it by it in saving_changes
    textarea.id = this.value;
}

function saving_changes(event) {
    // find the element that was clicked and get post_id and csrf token
    let post_id = this.value
    let parentDiv = this.closest('.single-post');
    let token = parentDiv.querySelector('input').value

    // get the new text by the id i assigned in edit_mode() function.
    let newText = document.getElementById(post_id);
    //fetch API
    fetch(`/edit-post/${post_id}`, {
        method: 'PUT',
        // CSRF token is sent with headers
        headers: {
                 'X-CSRFToken': token
        },
        body: JSON.stringify ({
            text: newText.value
        })
    })
    // convert JsonResponse from django view to json format
    .then(response => response.json())
    // update page with new information with response from server
    .then(result => {

        // change button functionality from save to edit again
        let saveButton = document.querySelector('#saving-changes');
        saveButton.removeEventListener('click', saving_changes);
        saveButton.addEventListener('click', edit_mode);
        saveButton.id = 'edit-button' + post_id;
        saveButton.innerText = 'Edit';

        // find the div, where the form is and change text, taking it from result of response
        let postText = parentDiv.querySelector('.post-text');
        postText.innerText = result.new_text;
        postText.style.display = 'block';

        // hide the div with textarea
        let editForm = parentDiv.querySelector('.edit-post-field');
        editForm.style.display = 'none';

        // show message if exists
        if (result.message) {
            let messageDiv = parentDiv.querySelector('.post-message');
            messageDiv.innerText = result.message;
            messageDiv.style.color = 'red';
            messageDiv.style.display = 'block';
            // set timeout to hide div after a number of microseconds
            setTimeout(function() {
                messageDiv.innerText = '';
            }, 2000);
        };
    });
}

function like_unlike(event) {
    // using slice, get id
    let post_id = (this.id).slice(4,);
    let parentDiv = this.closest('.single-post');
    // find csrf
    let token = parentDiv.querySelector('input').value;

    fetch(`/like-unlike/${post_id}`, {
        method: 'PUT',
        headers: {
            'X-CSRFToken': token
        },
        body: JSON.stringify ({
            like: true
        })
    })
    .then (response => response.json())
    .then (result => {

        // change the text to Liked or Like by getting it from the view's response with result.like
        this.innerHTML = result.like + ' ' + result.amount;
        if (result.message) {
            let messageDiv = parentDiv.querySelector('.post-message');
            messageDiv.innerText = result.message;
            messageDiv.style.color = 'red';
            messageDiv.style.display = 'block';
            // set timeout to hide div after a number of microseconds
            setTimeout(function() {
                messageDiv.innerText = '';
            }, 2000);
        };
    });
}

function follow(event) {
    event.preventDefault();
    let parent = this.closest('#follow-section');
    let token = parent.querySelector('input').value;
    let user_id = this.getAttribute('data');

    fetch(`/follow/${user_id}`, {
        method: 'PUT',
        headers: {
            'X-CSRFToken': token
        },
        body: JSON.stringify ({
            following: true
        })
    })
    .then (response => response.json())
    .then (result => {
        // change button name
        this.innerText = result.following;
    });
}
