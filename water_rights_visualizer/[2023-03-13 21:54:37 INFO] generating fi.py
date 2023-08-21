[2023-03-13 21:54:37 INFO] generating figure for year 1985 ROI water.right.1
[2023-03-13 21:54:37 ERROR] 'MultiPolygon' object is not iterable
Traceback (most recent call last):
  File "/home/ec2-user/Water-Rights-Visualizer/water_rights_visualizer/water_rights_visualizer.py", line 909, in water_rights
    generate_figure(
  File "/home/ec2-user/Water-Rights-Visualizer/water_rights_visualizer/water_rights_visualizer.py", line 692, in generate_figure
    ax.add_patch(generate_patch(ROI_latlon, affine))
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ec2-user/Water-Rights-Visualizer/water_rights_visualizer/water_rights_visualizer.py", line 216, in generate_patch
    polygon = list(polygon)[0]
              ^^^^^^^^^^^^^
TypeError: 'MultiPolygon' object is not iterable
[2023-03-13 21:54:37 WARNING] unable to generate figure for year: 1985
[2023-03-13 21:54:37 INFO] processing year 1986 at R