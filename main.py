import sys
import gi
import itertools
import argparse

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf

DRAG_HANDLES_SIZE = 10
ALIGN_SNAP_SIZE = 5


class Select2DApp(Gtk.Window):
    def __init__(self, **kwargs):
        super(Select2DApp, self).__init__()
        self.set_default_size(800, 600)

        self.set_title(kwargs["title"])
        self.opt_polyline = kwargs["polyline"]
        self.opt_polyline_closed = kwargs["polyline_closed"]
        self.opt_snap = kwargs["snap"]

        self.image_filename = None
        self.image = None

        self.point_positions = []
        self.dragging_point = None

        self.init_ui()

    def init_ui(self):
        vbox = Gtk.VBox()
        self.add(vbox)

        self.canvas_area = Gtk.DrawingArea()
        self.canvas_area.connect("draw", self.on_draw)
        self.canvas_area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK
        )
        self.canvas_area.connect("button-press-event", self.on_button_press)
        self.canvas_area.connect("button-release-event", self.on_button_release)
        self.canvas_area.connect("motion-notify-event", self.on_motion_notify)
        vbox.pack_start(self.canvas_area, True, True, 0)

        # Add a horizontal box for the checkbox and Confirm button
        hbox = Gtk.HBox()  # Increase spacing for the whole hbox container
        vbox.pack_start(hbox, False, False, 0)

        hbox.set_margin_top(5)
        hbox.set_margin_bottom(5)
        hbox.set_margin_start(5)
        hbox.set_margin_end(5)

        # Add the checkbox for snapping
        self.snap_checkbox = Gtk.CheckButton.new_with_label("Snapping")
        self.snap_checkbox.set_active(self.opt_snap)

        hbox.pack_start(self.snap_checkbox, False, False, 0)

        # Add the Confirm button with more padding and a primary style class
        confirm_button = Gtk.Button.new_with_label("Confirm")
        confirm_button.connect("clicked", self.on_confirm_button_clicked)
        hbox.pack_end(confirm_button, False, False, 0)

    def get_snapping_enabled(self):
        return self.snap_checkbox.get_active()

    def load_image(self, filename):
        try:
            self.image = GdkPixbuf.Pixbuf.new_from_file(filename)
            self.image_filename = filename
            self.canvas_area.queue_draw()
        except GLib.Error as e:
            print(f"Error loading image: {e}")

        self.point_positions = [
            (0, 0),
            (0, self.image.get_height()),
            (self.image.get_width(), self.image.get_height()),
            (self.image.get_width(), 0),
        ]

    def on_draw(self, area, cr):
        if self.image:
            # Calculate the aspect ratio of the image and drawing area
            image_aspect_ratio = self.image.get_width() / self.image.get_height()
            drawing_area_width = self.canvas_area.get_allocated_width()
            drawing_area_height = self.canvas_area.get_allocated_height()
            drawing_area_aspect_ratio = drawing_area_width / drawing_area_height

            # Calculate the scaling factor to fit the image inside the drawing area
            if image_aspect_ratio > drawing_area_aspect_ratio:
                scale_factor = drawing_area_width / self.image.get_width()
            else:
                scale_factor = drawing_area_height / self.image.get_height()

            # Calculate the translation to center the image inside the drawing area
            translate_x = (drawing_area_width - self.image.get_width() * scale_factor) / 2
            translate_y = (drawing_area_height - self.image.get_height() * scale_factor) / 2

            cr.save()
            cr.translate(translate_x, translate_y)
            cr.scale(scale_factor, scale_factor)

            # Draw the image
            Gdk.cairo_set_source_pixbuf(cr, self.image, 0, 0)
            cr.paint()

            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.set_line_width(1)

            # Draw points with crosses inside
            for x, y in self.point_positions:
                cr.rectangle(
                    x - DRAG_HANDLES_SIZE,
                    y - DRAG_HANDLES_SIZE,
                    DRAG_HANDLES_SIZE * 2,
                    DRAG_HANDLES_SIZE * 2,
                )
                cr.move_to(x - DRAG_HANDLES_SIZE, y)
                cr.line_to(x + DRAG_HANDLES_SIZE, y)
                cr.move_to(x, y - DRAG_HANDLES_SIZE)
                cr.line_to(x, y + DRAG_HANDLES_SIZE)
                cr.stroke()

            # Draw the outline of the full quadrilateral if four points are selected
            if self.opt_polyline:
                cr.move_to(*self.point_positions[0])
                for x, y in self.point_positions[1:]:
                    cr.line_to(x, y)

                if self.opt_polyline_closed:
                    cr.close_path()

                cr.set_line_width(1)
                cr.stroke()

            cr.restore()

    def on_button_press(self, widget, event):
        if event.button == 1:  # Left mouse button
            x, y = self.component_to_image_space(event.x, event.y)
            point_index, near = self.get_closest_point(x, y)

            self.point_positions[point_index] = (x, y)
            self.dragging_point = point_index

            self.canvas_area.queue_draw()

    def on_button_release(self, widget, event):
        self.dragging_point = None

    def on_motion_notify(self, widget, event):
        if self.dragging_point is not None:
            x, y = self.component_to_image_space(event.x, event.y)
            width = self.image.get_width()
            height = self.image.get_height()

            if self.get_snapping_enabled():
                # Check for snapping to points with the same x or y coordinate
                for i, (px, py) in enumerate(self.point_positions):
                    if i != self.dragging_point:
                        if abs(px - x) < ALIGN_SNAP_SIZE:
                            x = px
                        if abs(py - y) < ALIGN_SNAP_SIZE:
                            y = py

                # Check for snapping to the image borders
                if abs(x) < ALIGN_SNAP_SIZE:
                    x = 0
                elif abs(x - width) < ALIGN_SNAP_SIZE:
                    x = width
                if abs(y) < ALIGN_SNAP_SIZE:
                    y = 0
                elif abs(y - height) < ALIGN_SNAP_SIZE:
                    y = height

            self.point_positions[self.dragging_point] = (x, y)
            self.canvas_area.queue_draw()

    def on_confirm_button_clicked(self, widget):
        for x, y in self.point_positions:
            print(f"{round(x)}\t{round(y)}")
        Gtk.main_quit()

    def get_closest_point(self, x, y):
        def distance_squared(point):
            px, py = point
            return (px - x) ** 2 + (py - y) ** 2

        distances = [distance_squared(point) for point in self.point_positions]
        min_distance = min(distances)
        closest_index = distances.index(min_distance)

        return closest_index, min_distance < 25

    def image_to_component_space(self, image_x, image_y):
        # Calculate the aspect ratio of the image and drawing area
        image_aspect_ratio = self.image.get_width() / self.image.get_height()
        drawing_area_width = self.canvas_area.get_allocated_width()
        drawing_area_height = self.canvas_area.get_allocated_height()
        drawing_area_aspect_ratio = drawing_area_width / drawing_area_height

        # Calculate the scaling factor to fit the image inside the drawing area
        if image_aspect_ratio > drawing_area_aspect_ratio:
            scale_factor = drawing_area_width / self.image.get_width()
        else:
            scale_factor = drawing_area_height / self.image.get_height()

        # Calculate the translation to center the image inside the drawing area
        translate_x = (drawing_area_width - self.image.get_width() * scale_factor) / 2
        translate_y = (drawing_area_height - self.image.get_height() * scale_factor) / 2

        # Apply scaling and translation to convert from image to component space
        x = image_x * scale_factor + translate_x
        y = image_y * scale_factor + translate_y

        return x, y

    def component_to_image_space(self, x, y):
        # Calculate the aspect ratio of the image and drawing area
        image_aspect_ratio = self.image.get_width() / self.image.get_height()
        drawing_area_width = self.canvas_area.get_allocated_width()
        drawing_area_height = self.canvas_area.get_allocated_height()
        drawing_area_aspect_ratio = drawing_area_width / drawing_area_height

        # Calculate the scaling factor to fit the image inside the drawing area
        if image_aspect_ratio > drawing_area_aspect_ratio:
            scale_factor = drawing_area_width / self.image.get_width()
        else:
            scale_factor = drawing_area_height / self.image.get_height()

        # Calculate the translation to center the image inside the drawing area
        translate_x = (drawing_area_width - self.image.get_width() * scale_factor) / 2
        translate_y = (drawing_area_height - self.image.get_height() * scale_factor) / 2

        # Inverse scaling and translation to convert from component to image space
        image_x = (x - translate_x) / scale_factor
        image_y = (y - translate_y) / scale_factor

        return image_x, image_y


def main():
    parser = argparse.ArgumentParser(prog="select2d", description="Image points selector")
    parser.add_argument("image", help="Image file path")
    parser.add_argument("--title", "-t", default="Select a quadrilateral", help="Title to show on the window")
    # parser.add_argument("--points", "-p", type=int, default=4, help="Number of points to select")
    parser.add_argument("--polyline", "-l", action="store_true", help="Show the outline of the quadrilateral")
    parser.add_argument("--closed", "-c", action="store_true", help="Indicate if the drawn path is closed")
    parser.add_argument("--snap", "-s", action="store_true", help="Activate snapping on points")
    args = parser.parse_args()

    # Pass the title as an optional argument
    app = Select2DApp(
        title=args.title,
        # num_points=args.points,
        polyline=args.polyline,
        polyline_closed=args.closed,
        snap=args.snap,
    )
    app.load_image(args.image)
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
