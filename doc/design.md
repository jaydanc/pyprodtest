# Overview

## Composition

![alt text](/doc/res/architecture.svg)

**Key**
|Colour|Category|
|------|--------|
|Lime|HTML|
|Blue|JavaScript|
|Cyan|Data Model|

Figure 1 shows the composition of PyProdTest; it is made up of three logical groups that serve specific purposes:

1. Core: everything on the outside of the interfaces is the core of PyProdTest. It has the goal of capturing Pytest data and translating it into a domain model (test metadata defined in decorators for example are gathered here and placed into it's domain class `TestMetadata`). Additionally, when a request for input is made, it finds a provider (one-to-one relationship). Aside from this, it's only other job is to forward this information to the test observers (one-to-many relationship).
2. Test Observers: anything that wants to know about the data. In this architecture, we have a `WebServer` which wants to be kept up to date, and two report generators who want to know this information.
3. Input Provider: When input is requested, the assigned provider (in this case, `WebServer`) will handle the request.

This design makes it easier to expand what PyProdTest does, such as eventually adding a remote test observer. It also helps prevent breaking changes by limiting the number of modules which have this power; **care should be taken around the data model and interfaces**. Finally, it makes it easier to unit test our core functionality and observers/providers.