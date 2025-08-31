#!/usr/bin/env python3
import argparse
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib as mpl
from lxml import etree
from pykml.factory import KML_ElementMaker as KML
import zipfile
import os
import sys

# -----------------------------------------------------------
# Resource directory detection:
# Priority 1: Environment variable MY_SCR
# Priority 2: Directory where this script resides
# -----------------------------------------------------------
def _resource_dir():
    env_dir = os.environ.get("MY_SCR")
    if env_dir and os.path.isdir(env_dir):
        return os.path.abspath(env_dir)
    return os.path.dirname(os.path.abspath(__file__))

RES_DIR = _resource_dir()

def _res_path(filename: str) -> str:
    """Build absolute path for a static resource file inside RES_DIR."""
    return os.path.join(RES_DIR, os.path.basename(filename))


def vel2kml_color(value, vmin, vmax, cmap_name='jet_r'):
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    cmap = plt.get_cmap(cmap_name)
    rgba = cmap(norm(value))
    r, g, b, a = [int(255 * x) for x in rgba]
    return '{:02x}{:02x}{:02x}{:02x}'.format(a, r, g, b)


def read_csv_timeseries(csv_file):
    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.strip()
    date_cols = [col for col in df.columns if col.startswith('D')]
    dates = [col[1:5] + '-' + col[5:7] + '-' + col[7:9] for col in date_cols]
    ts_list = df[date_cols].values.tolist()
    lats = df['LAT'].values
    lons = df['LON'].values
    vels = df['VEL'].values
    vel_stds = df['VSDEV'].values
    coherence = df['COHER'].values
    return lats, lons, dates, ts_list, vels, vel_stds, coherence


def save_colorbar(vmin, vmax, cmap_name, out_file, label='Mean LOS velocity [mm/year]', figsize=(1.4, 6), fontsize=18):
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    fig.subplots_adjust(left=0.4, right=0.8, top=0.99, bottom=0.01)
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    cmap = mpl.cm.get_cmap(cmap_name)
    cb = mpl.colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, orientation='vertical')
    cb.set_label(label, fontsize=fontsize, color='black')
    cb.ax.yaxis.label.set_backgroundcolor('white')
    cb.ax.yaxis.label.set_color('black')
    cb.outline.set_edgecolor('black')
    cb.ax.tick_params(labelsize=fontsize - 2, colors='black')
    for tick in cb.ax.yaxis.get_major_ticks():
        tick.label1.set_color('black')
        tick.label1.set_backgroundcolor('white')
        tick.label1.set_fontsize(fontsize - 2)
    plt.savefig(out_file, dpi=600, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"Colorbar image saved to {out_file}")


def generate_colorbar_overlay(cbar_file='colorbar.png'):
    overlay = KML.ScreenOverlay(
        KML.name('Colorbar'),
        KML.Icon(KML.href(os.path.basename(cbar_file))),
        KML.overlayXY(x="0", y="0", xunits="fraction", yunits="fraction"),
        KML.screenXY(x="0", y="0", xunits="fraction", yunits="fraction"),
        KML.rotationXY(x="0", y="0", xunits="fraction", yunits="fraction"),
        KML.size(x="65", y="250", xunits="pixels", yunits="pixels")
    )
    return overlay


def generate_js_datastring(dates, dygraph_file, ts):
    dygraph_file = os.path.basename(dygraph_file)
    js_data_string = f"<script type='text/javascript' src='{dygraph_file}'></script>"
    js_data_string += """
        <div id='graphdiv'> </div>
        <style>
            .dygraph-legend{
                left: 230px !important;
                width: 265px !important;
            }
        </style>
        <script type='text/javascript'>
            g = new Dygraph( document.getElementById('graphdiv'),
            "Date, displacement\\n" +
    """
    for k, date in enumerate(dates):
        dis = ts[k]
        js_data_string += f"\"{date}, {dis}\\n\" + \n"
    js_data_string += """
    "",
       {
         width: 500,
         height: 300,
         axes: {
             x: {
                 axisLabelFormatter: function (d, gran) {
                     var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                     var date = new Date(d)
                     var dateString = months[date.getMonth()] + ' ' + date.getFullYear()
                     return dateString;
                 },
                 valueFormatter: function (d) {
                     var date = new Date(d)
                     var dateString = 'Date: ' + ('0' + date.getDate()).slice(-2) +
                                      '/' + ('0' + (date.getMonth() + 1)).slice(-2) +
                                      '/' + date.getFullYear()
                     return dateString;
                 },
                 pixelsPerLabel: 90
             },
             y: {
                 valueFormatter: function(v) {
                       return v.toFixed(2);
                 }
             }
         },
         ylabel: 'Cumulative displacement [mm]',
         yLabelWidth: 18,
         drawPoints: true,
         strokeWidth: 0,
         pointSize: 3,
         highlightCircleSize: 6,
         axisLabelFontSize: 12,
         xRangePad: 30,
         yRangePad: 30,
         hideOverlayOnMouseOut: false,
         panEdgeFraction: 0.0
       });
       </script>
    """
    return js_data_string


def get_description_string(lat, lon, v, vstd, disp, tcoh=None, font_size=4):
    des_str = f"<font size={font_size}>"
    des_str += f"Latitude: {lat:.6f}˚ <br /> \n"
    des_str += f"Longitude: {lon:.6f}˚ <br /> \n"
    des_str += " <br /> \n"
    des_str += f"Mean LOS velocity [mm/year]: {v:.2f} <br /> \n"
    des_str += f"Cumulative displacement [mm]: {disp:.2f} <br /> \n"
    if tcoh is not None:
        des_str += f"Coherence: {tcoh:.2f} <br /> \n"
    des_str += "</font> <br />  <br /> *Double click to reset plot <br /> <br />\n"
    return des_str


def create_kml_from_csv_colored(csv_file, dygraph_js_file, kml_out='output.kml', step=1,
                                 icon_file='shaded_dot.png', cbar_file='colorbar.png',
                                 vmin=None, vmax=None, cmap_name='jet', dot_scale=0.25):
    lats, lons, dates, ts_list, vels, vel_stds, coherence = read_csv_timeseries(csv_file)
    if vmin is None: vmin = float(min(vels))
    if vmax is None: vmax = float(max(vels))
    kml_doc = KML.Document()
    kml_doc.append(generate_colorbar_overlay(cbar_file))
    folder = KML.Folder(KML.name("InSAR Colored Points"))
    for i in range(0, len(lats), step):
        lat, lon = lats[i], lons[i]
        ts = ts_list[i]
        v = vels[i]
        vstd = vel_stds[i]
        tcoh = coherence[i]
        disp = ts[-1]
        desc = get_description_string(lat, lon, v, vstd, disp, tcoh)
        js_str = generate_js_datastring(dates, dygraph_js_file, ts)
        description = KML.description(desc + js_str)
        color = vel2kml_color(v, vmin, vmax, cmap_name)
        style = KML.Style(
            KML.IconStyle(
                KML.color(color),
                KML.scale(dot_scale),
                KML.Icon(KML.href(os.path.basename(icon_file)))
            )
        )
        point = KML.Point(KML.coordinates(f"{lon},{lat}"))
        placemark = KML.Placemark(style, description, point)
        folder.append(placemark)
    kml_doc.append(folder)
    kml_root = KML.kml()
    kml_root.append(kml_doc)
    with open(kml_out, 'w', encoding='utf-8') as f:
        f.write(etree.tostring(kml_root, pretty_print=True).decode('utf-8'))
    print(f"KML saved to {kml_out}")


def create_kmz_from_kml_and_files(kml_file, output_kmz, resource_files):
    with zipfile.ZipFile(output_kmz, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(kml_file, arcname='doc.kml')
        for rf in resource_files:
            zf.write(rf, arcname=os.path.basename(rf))
    print(f"KMZ saved to {output_kmz}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate KMZ from CSV time series")
    parser.add_argument("csv_file", help="Input CSV file")
    parser.add_argument("-vmin", type=float, required=True, help="Minimum velocity")
    parser.add_argument("-vmax", type=float, required=True, help="Maximum velocity")
    parser.add_argument("-step", type=int, default=100, help="Sampling step")
    parser.add_argument("-dot", type=float, default=0.25, help="Dot scale size")
    args = parser.parse_args()

    # Always create colorbar.png in current working directory
    save_colorbar(args.vmin, args.vmax, 'jet_r', 'colorbar.png',
                  label='Mean LOS velocity [mm/year]')

    create_kml_from_csv_colored(
        csv_file=args.csv_file,
        dygraph_js_file=_res_path('dygraph-combined.js'),
        kml_out='output_tmp.kml',
        step=args.step,
        icon_file=_res_path('shaded_dot.png'),
        cbar_file='colorbar.png',
        vmin=args.vmin,
        vmax=args.vmax,
        cmap_name='jet',
        dot_scale=args.dot
    )

    output_kmz = os.path.splitext(os.path.basename(args.csv_file))[0] + '.kmz'
    create_kmz_from_kml_and_files(
        kml_file='output_tmp.kml',
        output_kmz=output_kmz,
        resource_files=[
            _res_path('shaded_dot.png'),
            _res_path('dygraph-combined.js'),
            'colorbar.png'
        ]
    )
    os.remove('output_tmp.kml')
