# TiltEnhance

A suite of LandTech Tiltfiles, to accelerate end-to-end application development 🔥

## Wait, what is Tiltfiles?!

Tilt is a system for orchestrating a full local or remote Kubernetes\* environment for your applications.
It's cool. Look, check it out: https://tilt.dev/

- `tilt up` spins up a full remote environment 🎁 as specified in you project's _Tiltfile_

- While Tilt is running it will intelligently and quickly update 🔄 your remote environment in step with local changes

- While Tilt is stopped your environment will persist, but you'll get no more live updates 🏚

- `tilt down [--delete-namespaces]` tears down aforementioned environment 👍 🗑

\*it's geared solely towards Kubernetes resource management, which brings us nicely to our next point...

## Why do I need TiltEnhance then?

While adopting Tilt we've found a few limitations, where it doesn't quite fit our existing workflows. Luckily for us, extending Tilt is a breeze.

_I want to create a temoporary credstash secret, and have it clean up on `tilt down`_
\> We got you. Take a look in the **_local_resource_ext_** Tiltfile. I'll explain how to use it in a min...

_I want to do what she said 👆 but with S3 buckets_
\> Yep - same place

_In fact I want to create literally any custom resource, and define a custom teardown function_
\> This is all the same use case. Anything else?

_I've heard Tilt doesn't natively understand helm install hooks_
\> We got you! Look at **_helm_hooks_**

_Ooh, what about running containerised tasks (tests) locally and in the cluster_
\> Yep, **_docker_task_** is your guy

_I want to do some other features that aren't document_
\> Probably in there too, but please add them (with tests) if not! 😁

## How on earth do I use this?!

Great question. If you haven't you'll need to make yourself a `Tiltfile`. [Here's the docs; figure it out](https://docs.tilt.dev/api.html).

You'll then need to register this extensions repo like so:
```py
v1alpha1.extension_repo(name='tiltenhance', url='https://github.com/landtechnologies/tiltenhance')
```

Next let's import some stuff. If you've been reading the tilt docs, you'll know you can require _Tiltfiles_ with `load(...)`

Pop something like this in your _Tiltfile_ to use the `docker_remote` resource from the `docker_task` extension.

```py
## Register
v1alpha1.extension(name='docker_task', repo_name='tiltenhance', repo_path='docker_task')

## Import
load("ext://tiltenhance/docker_task", "docker_remote")

## Use
docker_remote("my-important-task", "./path/to/Dockerfile")
```

(We know that registering the repo and extension, and then loading the function is wordy, but we'll see what we can do about that later.)

## Can I contribute?

Yeah, we got some good tests going on. Keep those going, and maybe flesh out this section 👈
