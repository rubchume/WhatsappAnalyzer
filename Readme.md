# Introduction

Have you ever realized that in a Whatsapp group chat, there is always someone (let's call her Alice) who almost always is the first one to talk after someone else (let's call him John) says something?

WhatsappAnalyzer is a web application that analyzes the intensity (warmth, closeness) of relationships between the members of a Whatsapp group.

It uses chat export files and anlyzes the order of messages (how many times a member responded after another member). The strong assumptions is that the more intense the relationship between two users, the more messages they send back and forth.

The results are represented visually as a network connected by red or blue links (warm or cold relationships).

The app is already prepared to be deployed as-is on the PaaS [Heroku](https://www.heroku.com/).

# Approach

## Technical details
It has been developed by using the Django framework as the web backend.

The visualizations use Python package Plotly and Dash.
The cleaning and processing of data relies heavily on Pandas and Numpy packages.

The deployment has been done in Heroku.

## Analysis process
The analysis step models each chat as a Markov probabilistic process and uses linear algebra (eigendecomposition) to find the warmth coefficients.

A Markov process is a mathematical abstraction to model a process where there are some states a variable can have (like the last message in a chat being written by Alice, John, or Charles), and in each iteration, there is a specific probability that the next message belongs to each one of them. Hence the probabilities of going from one state to another can be represented in a matrix:

|         | Alice | John | Charles |
|---------|-------|------|---------|
| Alice   | X     | 0.5  | 0.5     |
| John    | 0.9   | X    | 0.1     |
| Charles | 0.5   | 0.5  | X       |

This is just a made up example. The thing is, in real chats we can estimate this matrix using the Maximum Likelihood estimator (which fortunately can be calculated using some simple linear algebra with eigenvalue decomposition).

In other words, the application compares the actual number of messages of _User A_ followed by messages of _User B_, with the expected number under the hypothesis that messages are just random (generated by a multinomial distribution https://en.wikipedia.org/wiki/Multinomial_distribution). The probability that a given message is written by a given user is estimated as the proportion of messages of that user (Maximum Likelihood Estimator for the Multinomial distribution).

It is important to highlight that the computations take in account how often a person talks in general.
If   Charles just spends his days talking in the group, of course most of the messages of Alice or John will be followed by a message of Charles,
but that does not mean that Charles has a preference for Alice or John.
The computations take in account that bias and compensate for that.

# Conclusions

The main lessons learned during the development of this app are:
- Use loosely coupled architecture to be able to deploy the app in different platforms seamlessly. Fortunately Heroku makes this very easy.
- Plotly and Dash still needs to mature in order to fully support this type of enhanced graph visualizations. However they did a very good job.

Regarding the lessons learned during analysis, it depends on the specific Whatsapp group. On the personal side I found very interesting how the sympathies one notices intuitively are very clear once you run the analysis. Numbers do not lie.

As a future path of improvement, I would suggest to investigate further the use of Dash with many simultaneous users.

# How to use

The first step is to upload a Whatsapp chat export file of a group chat ([video tutorial](https://www.youtube.com/watch?v=-Ald352nhao)).

Once you do it the app draws a graph where each user is represented as a circle and the connection between them as a lines.
The area of each circle is proportional to the number of messages sent by the user.

The lines that go from once circle to another represent the _intensity_ of the communication between each user. The _intensity_ is calculated looking at the chat as a sequence of messages. The application counts how many messages from a given user are followed by messages of each of the rest of users.

If the actual number of back and forth messages is approximately the same as the expected one, the line that joins the circles of both users will be white.

If it is higher, it will be red (the relationship is _hot_).

If it is lower, it will be blue (the relationship is _cold_).

![WhatsappGraphExplanation](sample_data/WhatsappGraphExplanation.png)

You can click on the circles to show them or disable them.

The next is an example with anonymous users:
![Example with anonymous users](sample_data/PutassosGráfico.png)

The Whatsapp chat export file is deleted after it is processed, i.e. it is not stored.

It will take some seconds until the file is processed.
If you do not see anyting after a while, just refresh. It is just a minor bug.
