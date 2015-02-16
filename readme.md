scan2pdf
========

A script to automate scanning documents.
Not related to [gscan2pdf](http://freecode.com/projects/gscan2pdf),
except that they both do similar things.

TODO:

* rewrite the path and available fns so they make sense
* remove blank pages
* add an OCR step
* what were these for? should I keep them?
  '-level', '15%,85%'
  '-depth', '2'
* get it to stop with the 01 suffix
* combine mv + xdg-open as "finish" or something
* configurable extension so I can use png for notebook pages?
* pass any extra options along to scanimage
* add a command line flag for additional rotation (if easy)
