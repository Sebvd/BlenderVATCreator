# BlenderVATCreator

## Contents
Downloading the plugins
Exporting VATs
Optimizing VATs
Common errors

## Downloading the plugins
### Downloading the Blender plugin
Download the ZIP from this GitHub directory or on Gumroad.
In Blender, go to *edit > Preferences > Add-ons > Install from disk*
<img width="660" height="436" alt="afbeelding" src="https://github.com/user-attachments/assets/0544b320-d25b-4e09-b62d-57f12a67e863" />
The plugin should now be good to go.

### Downloading the Unreal Engine plugin
Download the Plugin folder form the GitHub. Create a new folder in your Unreal project folder called "Plugins", and paste the folder there.

## Exporting VATs
### Creating the files with the Blender plugin
<img width="407" height="170" alt="afbeelding" src="https://github.com/user-attachments/assets/031e5330-d761-4906-aec7-648c6dbd5099" />
By opening up the vat tools tab, you will find the main window for the VAT tools. To properly configure your VAT, you have a list of settings to your disposal:
- Frame Start: The starting frame of your simulation.
- Frame End: The ending frame of your simulation
- Frame Spacing: How much "space" in between each frame. For example, imagine a frame range between 1 and 10. If frame spacing is set to 1, this range would be "1,2,3,..10". But if set to 3, this would be "1,4,7,10". This allows you to reduce the FPS in your scene.
- VAT type: The type of vertex animation:
- + SoftBody: For softbody simulations such as cloth.
  + RigidBody: For rigidbody simulations such as destruction.
  + Fluid: For dynamic simulations such as fluids.

Texture & JSON settings: These settings help you convert between different coordinate spaces for your target engine.
<img width="412" height="176" alt="afbeelding" src="https://github.com/user-attachments/assets/59171b9e-7761-4932-ab67-a2d5e6ef37bb" />
You can click the Icon in the top right corner to automatically select a preset for some of the main game engines.
- Target coords: Target coordinate system axis order.
- Flip coords: Whether or not to negate the x, y or z components.
- Max U: Maximum size of the target position texture.
- Max U (Data): Only applicable to fluid simulations. Maximum size of the target data texture.

Mesh settings: These settings are applicable to the VAT mesh and how it behaves over the duration of the VAT simulation.
<img width="411" height="286" alt="afbeelding" src="https://github.com/user-attachments/assets/d62fb4a4-0f8c-433f-b967-243fac8305ce" />
- Rest pose: The pose of the simulation without any of the animations applied.
- Split at hard edges: Because VATs are determined per-vertex, the normals of the mesh are stored per-vertex as well, causing vertex normals that are always smooth. If you tick this box, the vertices are split so we can get hard edges, at the cost of a little bit of extra performance and texture size.
- LODs: How many extra LOD meshes to generate. These are stored as separate files. Use the "reduction rate" parameter to determine how strong the polygons should be reduced.

Export settings: Settings on how to export and store your VAT files. Note that this might look a bit different for every VAT type. Every individual export section has a checkbox. Unchecking it will prevent the plugin from exporting them.
<img width="406" height="328" alt="afbeelding" src="https://github.com/user-attachments/assets/b26361b2-07f8-45af-8dee-1d31578cedd3" />
- Output directory: Which directory to store your files in.
- VAT mesh: The target name of the VAT mesh. Uncheck the checkbox if you do not wish to export this.
- Simulation DATA JSON file: The target name of the VAT JSON file. This file contains necessary data that allows us to properly set up our VAT simulation inside of our target engine.
- VAT textures: These are different depending on the VAT type you have selected on the top. For each texture, you can create a file name and a file format.

Exporting:
Once you have adjusted all the settings to your liking, you can hit the "export" button. There are some important "catches" you need to be aware of:
- Please keep the polycount of your meshes in mind. High polycounts not only take really long to compute, but could also result in unusable VAT files. For example, high polycounts can create really big VAT textures, which will most definitely cause precision errors in the shader. For that reason, please have a moderate polycount (e.g., you are already getting high around the 30K-50K mark). (This does not apply to rigidbody simulations - for that its main bottleneck is the number of individual objects).
- Depending on the complexity of the simulation and the number of frames, computation might take quite long. This goes especially for fluid simulations.

### Assembling the VAT simulation in Unreal Engine


