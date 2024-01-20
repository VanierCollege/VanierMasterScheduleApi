# Vanier Master Schedule Api

This is a simple Python wrapper for the Vanier master schedule. You can browse using your terminal or integrate it with something else (for example notify you if seats are available).

This was made to have *some* fun in a time when registration is not so great, to say the least, where schedules are *awful* with *no* available GenEd courses...

#### How To Use
Using this wrapper requires creating a file named `vaniermasterschedule.securekey` with the value of a `base64SecureConfiguration`. At the time of writing, you can get this by inspecting the payload of a request sent to `c7a13072-c94f-ed11-bba3-0022486daee2` in your dev console. 


#### TODO
- [ ] Docstrings and ReadMe documentation
- [ ] ReadMe examples
- [ ] Filtering support (from the master schedule)
- [ ] Searching support (from the master schedule)
- [ ] Sorting support (from the master schedule)
- [ ] Improve fetch handling

#### Versioning
This wrapper is still in its early stage and future commmits may introduce breaking changes.

<hr>

*This project is made by a student and is by no means an official way to access the master schedule.*
