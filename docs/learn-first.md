# Learn This First

Do not try to understand everything at once. Start with one endpoint and one request flow.

## The first thing to learn

Focus only on the `/chat` flow first.

### Goal
Understand this simple chain:

1. User sends a message
2. The app receives it
3. The app sends it to the model
4. The model returns an answer
5. The app sends that answer back to the user

## What to study first

### 1. The route
Read the chat route and understand what input it accepts.

### 2. The runner
Understand how the app sends the request to the model and gets the response back.

### 3. The response shape
Understand what the user receives back from the API.

## What to ignore for now

Do not focus on:

- RAG
- MCP
- multi-agent flow
- advanced architecture details

Those will be easier once this one flow is clear.

## A simple mental model

Think of it like this:

- User input → app → model → answer → response

That is the foundation.

## How to know you understand it

You should be able to explain these three lines clearly:

- What does the user send?
- What does the app do with it?
- What does the user get back?
