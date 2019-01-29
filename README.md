# autoQC

This repo contains a set of scripts developed by [CAMDU](http://www.warwick.ac.uk/camdu) to help automate quality control tasks on our microscopes. 


## Getting Started

auto_PSF.py - Just download it and run inside Fiji. It will look for files containing the string "psf" on their filenames and run for the number of beads required on those. The output is "summary_psf.csv" with one line per bead containing X/Y/Z resolution in um.

auto_FOV.py - Just download it and run inside Fiji. It will look for files containing the string "fov" on their filenames and run on those, with one line output for each file. The output is "summary_fov.csv" with one line per FOV image, containing the relative intensity of the dimmest corner compared to the centre.

### Prerequisites

auto_PSF.py - requires [MetroloJ](http://imagejdocu.tudor.lu/doku.php?id=plugin:analysis:metroloj:start) installed with the [iText library v.2.1.4](http://imagejdocu.tudor.lu/lib/exe/fetch.php?media=plugin:analysis:metroloj:itext-2.1.4.jar). Newest Fiji version is always recommended.
auto_FOV.py - requires [MetroloJ](http://imagejdocu.tudor.lu/doku.php?id=plugin:analysis:metroloj:start) installed with the [iText library v.2.1.4](http://imagejdocu.tudor.lu/lib/exe/fetch.php?media=plugin:analysis:metroloj:itext-2.1.4.jar). Newest Fiji version is always recommended.


## Contributing

Feel free to copy, remix, submit pull requests and so on!


## Authors

* **Erick Martins Ratamero** - *Scripting* 
* **Claire Mitchell** - *Experimental input, workflow* 



## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
