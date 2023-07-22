# 2D Image Selector

<p align="center">
  <img src="./screenshot.png" width="75%"/>
</p>

Select2d is a simple GTK widget written in Python that allows users to load an image and interactively select a quadrilateral by placing four draggable points on the image. The coordinates of the selected quadrilateral are printed to standard output after confirmation.

## About this project
 
I wanted to make a small GTK application for a while but I had problems finding good guides and tutorials about it. So this project was started by chatting with **ChatGPT** by gradually adding features. And it looks like its really good at writing such code by hand. The most outstanding thing is that at a certain point I told it to update the function that handles point dragging and add support for snapping and it did it! So

> Python + GTK + ChatGPT = :heart:

Ironically this can be done in something like three lines of Mathematica code

```mathematica
DynamicModule[{pt1 = {0, 0}, pt2 = {100, 0}, pt3 = {100, 100}, pt4 = {0, 100}},
  LocatorPane[Dynamic[{pt1, pt2, pt3, pt4}],
    Show[img, Graphics[{Directive[Red, Opacity[0.5]], EdgeForm[{Red, Thickness[2]}], Polygon[Dynamic[{pt1, pt2, pt3, pt4}]]}]]
  ]
]
```

## Usage

- Clone the repository:

    ```bash shell
    $ git clone https://github.com/aziis98/gtk-select
    ```

- Create and activate a virtual environment

    ```bash shell
    $ python -m venv env
    $ source env/bin/activate
    ```

- Install the required dependencies:

    ```bash shell
    $ pip install -r requirements.txt
    ```

- Run the application with the desired options:

    ```bash shell
    $ ./select2d [--title <title>] [--polyline] [--closed] <image>
    ```

- The output contains the four points in the image.

### Arguments

- `<image>`: The path to the image file you want to load and select points on.

### Optional Arguments

- `--title` or `-t`: Set a custom window title for the application (default: "2D Image Selector").

- `--polyline` or `-s`: Show the outline of the quadrilateral that is formed by connecting the selected points.

- `--closed` or `-c`: Indicate if the drawn path should be closed, forming a closed polygon. This option is relevant only when displaying the quadrilateral with the previous option.

## Usage Example

To select a region of interest in the image "example.png" and display the outline of the selected region with a custom title "Region Selector" use the following command:

```bash shell
$ ./select2d example.png --title "Region Selector" --polyline
```

