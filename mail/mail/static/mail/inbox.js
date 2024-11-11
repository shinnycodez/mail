document.addEventListener('DOMContentLoaded', function() {

  // Use buttons to toggle between views
  document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
  document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
  document.querySelector('#archived').addEventListener('click', () => load_mailbox('archive'));
  document.querySelector('#compose').addEventListener('click', compose_email);

  document.querySelector("#compose-form").addEventListener("submit", function(event) {

    event.preventDefault();
    
    fetch('/emails', {
      method: 'POST',
      body: JSON.stringify({
        recipients: document.querySelector('#compose-recipients').value,
        subject: document.querySelector('#compose-subject').value,
        body: document.querySelector('#compose-body').value
      }),
    })
    .then(response => response.json())
    .then(result => {
      console.log(result);
    })
    .then(() => {
      load_mailbox('sent');
    }) 
    .catch(error => console.log("Error:", error));
  });

  
  // By default, load the inbox
  load_mailbox('inbox');
});

function compose_email() {

  // Show compose view and hide other views
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#email-details-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'block';

  // Clear out composition fields
  document.querySelector('#compose-recipients').value = '';
  document.querySelector('#compose-subject').value = '';
  document.querySelector('#compose-body').value = '';

}

function load_mailbox(mailbox) {
  
  // Show the mailbox and hide other views
  document.querySelector('#emails-view').style.display = 'block';
  document.querySelector('#compose-view').style.display = 'none';
  document.querySelector('#email-details-view').style.display = 'none';

  // Show the mailbox name
  document.querySelector('#emails-view').innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>`;
  fetch(`/emails/${mailbox}`)
  .then(response => response.json())
  .then(emails => {
    // Print emails
    console.log(emails);

    emails.forEach(email => {

      const emailBar = document.createElement("div");
      emailBar.className = email["read"] ? 'email-bar-read' : 'email-bar';
      emailBar.addEventListener('click', () => email_details(email['id']));

      const emailSender = document.createElement("div");
      emailSender.className = email["read"] ? 'email-sender-read' : 'email-sender';
      emailSender.textContent = email['sender'];

      const emailSubject = document.createElement("div");
      emailSubject.className = email["read"] ? 'email-subject-read' : 'email-subject';
      emailSubject.textContent = email["subject"];

      const emailTimestamp = document.createElement("div");
      emailTimestamp.className = email["read"] ? 'email-timestamp-read' : 'email-timestamp';
      emailTimestamp.textContent = email["timestamp"];

      emailBar.append(emailSender);
      emailBar.append(emailSubject);
      emailBar.append(emailTimestamp);
      document.querySelector("#emails-view").append(emailBar);


    });
  })
  .catch(error => console.log('Error:', error));
}

function email_details(id) {

  document.querySelector('#email-details-view').style.display = 'block';
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'none';
  

  document.querySelector(".email-sender-det").innerHTML = '';
  document.querySelector(".email-recipients-det").innerHTML = '';
  document.querySelector(".email-subject-det").innerHTML = '';
  document.querySelector(".email-timestamp-det").innerHTML = '';
  document.querySelector(".email-body-det").innerHTML = '';

  fetch(`/emails/${id}`, {
    method: 'PUT',
    body: JSON.stringify({
        read: true
    })
  });

  fetch(`/emails/${id}`)
  .then(response => response.json())
  .then(email => {
    console.log(email);
    
    document.querySelector(".email-sender-det").innerHTML = `<strong>Sender:</strong> ${email["sender"]}`;
    document.querySelector(".email-recipients-det").innerHTML = `<strong>Recipients:</strong> ${email["recipients"]}`;
    document.querySelector(".email-subject-det").innerHTML = `<strong>Subject:</strong> ${email["subject"]}`;
    document.querySelector(".email-timestamp-det").innerHTML = `<strong>Sent:</strong> ${email["timestamp"]}`;
    document.querySelector(".email-body-det").innerHTML = `<p> ${email["body"]} </p>`;

    const replyButton = document.querySelector(".reply");
    replyButton.addEventListener("click", () => reply(email));

    let archiveDiv = document.querySelector(".archive-div");
    let unarchiveDiv = document.querySelector(".unarchive-div");
    if (email["sender"] != document.querySelector("#user-email").value){
      if (email["archived"] === true) {
        if (archiveDiv) { // Check if archiveDiv exists
          archiveDiv.style.display = 'none';
        }
        if (unarchiveDiv) { // Check if unarchiveDiv exists
          unarchiveDiv.style.display = 'inline-block';
        }
      } else {
        if (archiveDiv) { // Check if archiveDiv exists
          archiveDiv.style.display = 'inline-block';
        }
        if (unarchiveDiv) { // Check if unarchiveDiv exists
          unarchiveDiv.style.display = 'none';
        }
    }
      archiveDiv.addEventListener("click", () => archive(email));
      unarchiveDiv.addEventListener("click", () => unarchive(email));
    } else {
      archiveDiv.style.display = 'none';
      unarchiveDiv.style.display = 'none';
    }

    
  })


  .catch(error => console.error(error));
}

function archive(email){

  fetch(`/emails/${email["id"]}`, {
    method: 'PUT',
    body: JSON.stringify({
        archived: true
    })
  })
  window.location.reload();
  load_mailbox("inbox");
}

function unarchive(email){

  fetch(`/emails/${email["id"]}`, {
    method: 'PUT',
    body: JSON.stringify({
        archived: false
    })
  })
  window.location.reload();
  load_mailbox("inbox");
}


function reply(email) {

  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#email-details-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'block';

  fetch(`/emails/${email["id"]}`)
  .then(response => response.json())
  .then(email => {
    document.querySelector('#compose-recipients').value = `${email["sender"]}`;
    document.querySelector('#compose-subject').value = `Re: ${email["subject"]}`;
    document.querySelector('#compose-body').value = `On ${email["timestamp"]} ${email["sender"]} wrote: ${email["body"]}`;
  })

  .catch(error => console.error(error));
}