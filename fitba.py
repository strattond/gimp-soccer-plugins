#!/usr/bin/env python3

import gi

gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
import json
import sys

from gi.repository import Gimp, GimpUi, Gio, GLib, Gtk

score_table_proc  = "plug-in-football-tables"
next_fixture_prc  = "plug-in-football-fixture"
team_fixture_prc  = "plug-in-football-fixture-team"
draw_football_pr  = "plug-in-football-shape"
fixture_res_proc  = "plug-in-football-results"
infographic_proc  = "plug-in-football-infographic"
team_info_proc    = "plug-in-football-team-infographic"
chevron_proc      = 'plug-in-football-chevron'

class JsonFileChooser:
  def __init__(self, title="Select JSON File"):
    self.title = title
    self.filename = None
  def run(self):
    GimpUi.init("json-file-chooser")
    dialog = Gtk.Dialog( title=self.title, flags=0 )
    dialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("_OK", Gtk.ResponseType.OK)
    content = dialog.get_content_area()
    hbox    = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    content.add(hbox)
    # Text entry
    entry = Gtk.Entry()
    entry.set_hexpand(True)
    hbox.pack_start(entry, True, True, 0)
    # Browse button
    browse_btn = Gtk.Button(label="Browse…")
    hbox.pack_start(browse_btn, False, False, 0)
    # Browse handler
    def on_browse_clicked(button):
      chooser = Gtk.FileChooserDialog(
        title="Choose JSON File",
        action=Gtk.FileChooserAction.OPEN
      )
      chooser.add_buttons( "_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.OK )
      flt = Gtk.FileFilter()
      flt.set_name("JSON files")
      flt.add_pattern("*.json")
      chooser.add_filter(flt)
      if chooser.run() == Gtk.ResponseType.OK:
        file = chooser.get_file()
        if file:
          entry.set_text(file.get_path())
      chooser.destroy()
    browse_btn.connect("clicked", on_browse_clicked)
    dialog.show_all()
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
      self.filename = entry.get_text()
    dialog.destroy()
    return self.filename

def create_text_layer_at( image, text_value, font, ptSize, parentLayer, posX, posY ):
  text_layer = Gimp.TextLayer.new(image, text_value, font, ptSize, Gimp.Unit.point())
  image.insert_layer( text_layer, parentLayer, -1 )
  text_layer.set_line_spacing(10.0)
  text_layer.set_offsets( posX, posY )
  return text_layer

def create_image_layer_at( image, folder, club, parentLayer, squareSize, posX, posY ):
  file = Gio.File.new_for_path( folder + "\\" + club + ".png" )
  hlayer = Gimp.file_load_layer(Gimp.RunMode.NONINTERACTIVE, image, file)
  image.insert_layer(hlayer, parentLayer, -1 )
  hX, hY = newDimensions( hlayer, squareSize )
  hlayer.scale( hX, hY, True )
  hlayer.set_offsets( posX, posY )
  return hlayer
  
# Extracts the columnar data
def extract_column(data, attr):
  if not data:
    return []
  return [str(record[attr]) for record in data]

def coords_to_vec2_list(flat_coords):
  return [(flat_coords[i], flat_coords[i + 1]) for i in range(0, len(flat_coords), 2)]

def createNewLayer( image, name, width, height, parent=None ):
  layer = Gimp.Layer.new( image, name, width, height, Gimp.ImageType.RGBA_IMAGE, 100, Gimp.LayerMode.NORMAL )
  image.insert_layer( layer, parent, -1 )
  return layer

def createVecLayer( image, path, parent=None ):
  layer = Gimp.VectorLayer.new( image, path )
  image.insert_layer( layer, parent, -1 )
  return layer

def chevron_up( x, y, width, height ):
    return [
      ( x, y + height ),
      ( x + width, y ),
      ( x + ( 0.75 * width ), y  ),
      ( x + width, y + ( 0.25 * height ) ),
      ( x + width, y ),
    ]
    #halfW = width  / 2
    #halfH = height / 2
    #return [
    #  ( x - halfW,       y + height ),
    #  ( x - (halfW / 2), y + halfH  ),
    #  ( x,               y + ( halfH * 1.5 )  ),
    #  ( x + (halfW / 2), y + ( halfH * 1.5 )  ),
    #  ( x + width, y ),
    #  ( x + ( halfW * 1.25 ), y ),
    #  ( x + width, y + ( 0.5 * halfH ) ),
    #  ( x + width, y ),
    #]
    #halfW = width / 2
    #return [ 
    #        (x - (2*width), y + 1.5 * height),              # End point left
    #        (x - (width+halfW), y + height),              # End point left
    #        (x - width, y + 0.75 * height),              # End point left
    #        (x - halfW, y + height),              # End point left
    #        (x, y),                                 # Mid point
    #        (x + halfW, y + height ),              # End point right
    #        (x + width, y + 0.75 * height ),              # End point right
    #        (x + (width+halfW), y + height),              # End point left
    #        (x + (2*width), y + 1.5 * height),              # End point left
    #]

def draw_chevron_up( image, x, y, width, height, color ):
  points = chevron_up( x=x, y=y, height=width, width=height )
  neon_gradient_fill( image=image,
                      points=points,
                      color1=color,   # lime
                      color2=color,   # emerald
                      glow_px=40,
                      feather_px=20,
                      name="neon_up"
    )

def chevron_down(x, y, width, height ):
    return [
      ( x,       y ),
      ( x + width, y + height ),
      ( x + ( 0.75 * width ), y + height ),
      ( x + width, y + ( 0.75 * height ) ),
      ( x + width, y + height ),
    ]
    #halfW = width  / 2
    #halfH = height / 2
    #return [
    #  ( x - halfW,       y ),
    #  ( x - (halfW / 2), y + halfH  ),
    #  ( x,               y + ( halfH * 0.5 )  ),
    #  ( x + (halfW / 2), y + ( halfH * 0.5 )  ),
    #  ( x + width, y + height ),
    #  ( x + ( halfW * 1.25 ), y + height ),
    #  ( x + width, y + ( 1.5 * halfH ) ),
    #  ( x + width, y + height ),
    #]
    #halfW = width / 2
    #return [ 
    #        (x - (2*width), y - 1.5 * height),              # End point left
    #        (x - (width+halfW), y - height),              # End point left
    #        (x - width, y - 0.75 * height),              # End point left
    #        (x - halfW, y - height),              # End point left
    #        (x, y),                                 # Mid point
    #        (x + halfW, y - height ),              # End point right
    #        (x + width, y - 0.75 * height ),              # End point right
    #        (x + (width+halfW), y - height),              # End point left
    #        (x + (2*width), y - 1.5 * height),              # End point left
    #]

def draw_chevron_down( image, x, y, width, height, color ):
  points = chevron_down( x=x, y=y, height=width, width=height )
  neon_gradient_fill( image=image,
                      points=points,
                      color1=color,   # lime
                      color2=color,   # emerald
                      glow_px=40,
                      feather_px=20,
                      name="neon_up"
    )

def catmullRomLine( p0, p1, p2, p3, t, t2, t3 ):
  return 0.5 * (
                  ( 2    * p1 ) +
                  ( -p0  + p2 ) * t +
                  ( 2*p0 - 5*p1 + 4*p2 - p3 ) * t2 +
                  ( -p0  + 3*p1 - 3*p2 + p3 ) * t3
  )

def catmullRomInterpolate( p0, p1, p2, p3, steps=20 ):
  points = []
  for step in range( steps + 1 ):
    t = step / steps # 0..1
    t2 = t ** 2
    t3 = t2 * t
    # We need continuity between points, so Bezier is out
    # https://en.wikipedia.org/wiki/Catmull%E2%80%93Rom_spline
    # Ah, the joys of matrix math coming back
    # 
    sampleX = catmullRomLine( p0[0], p1[0], p2[0], p3[0], t, t2, t3 )
    sampleY = catmullRomLine( p0[1], p1[1], p2[1], p3[1], t, t2, t3 )
    points.append( ( sampleX, sampleY ) )
  return points

def neon_gradient_fill( image, points, color1, color2, glow_px, feather_px, name, withSpline = False ):

  brushSize   = 20
  orgLineWith = Gimp.context_get_brush_size()
  Gimp.context_set_brush_size( brushSize )
  curFG = Gimp.context_get_foreground()
  stroke = createNewLayer( image, name + "_stroke", image.get_width(), image.get_height() )
  geglColor1 = Gimp.color_parse_hex( color1 )
  Gimp.context_set_foreground( geglColor1 )  # solid red

  if( withSpline ):
    fullPoints = []
    for p0, p1, p2, p3 in zip(points, points[1:], points[2:], points[3:] ):
      interPoints = catmullRomInterpolate( p0, p1, p2, p3 )
      for x, y in interPoints:
        fullPoints.extend( [x, y] )

    Gimp.airbrush( stroke, 75, fullPoints )

    # And let's debug the control points
    #Gimp.context_set_brush_size( 3 * brushSize )
    #geglColor2 = Gimp.color_parse_hex( color2 )
    #Gimp.context_set_foreground( geglColor2 )  # solid red
    #for i in range( len( fullPoints ) ):
    #  Gimp.pencil( stroke, [ fullPoints[i], fullPoints[i + 1], fullPoints[i], fullPoints[i + 1] ] )
    #  i += 1
    for i, (x, y) in enumerate(points):
      nxColor = Gimp.color_parse_hex( f"#{i * 20:02X}{i * 20:02X}{i * 20:02X}")
      Gimp.context_set_foreground( nxColor )  # solid red
      Gimp.pencil( stroke, [ x, y, x, y ] )
  else:
    fullPoints = []
    for x, y in points:
      fullPoints.extend( [x, y] )
    Gimp.pencil( stroke, fullPoints )
    
  
  Gimp.context_set_brush_size( orgLineWith )
  Gimp.context_set_foreground( curFG )
  


def create_card( image, grpLayer, xPos, yPos, width, height, color="#FFFF00" ):
  bg_layer = Gimp.Layer.new(image, "Card", width, height, Gimp.ImageType.RGBA_IMAGE, 50, Gimp.LayerMode.NORMAL)
  image.insert_layer( bg_layer, grpLayer, -1 )
  bg_layer.set_offsets( xPos, yPos )

  # Set background color (red with 50% transparency)
  curFG = Gimp.context_get_foreground()
  yellow = Gimp.color_parse_hex( color )
  Gimp.context_set_foreground(yellow)  # Red, 50% alpha
  bg_layer.edit_fill(Gimp.FillType.FOREGROUND)
  Gimp.context_set_foreground(curFG)

def create_highlight_row(image, grpLayer, xPos, yPos, width, height):
  # Create a background layer for the matching row
  bg_layer = Gimp.Layer.new(image, "Oxley Woo", width, height, Gimp.ImageType.RGBA_IMAGE, 50, Gimp.LayerMode.NORMAL)
  image.insert_layer( bg_layer, grpLayer, -1 )
  bg_layer.set_offsets( xPos, yPos )

  # Set background color (red with 50% transparency)
  curFG = Gimp.context_get_foreground()
  green = Gimp.color_parse_hex( "00FF00" )
  Gimp.context_set_foreground(green)  # Red, 50% alpha
  bg_layer.edit_fill(Gimp.FillType.FOREGROUND)
  Gimp.context_set_foreground(curFG)
  
def create_player_colour(image, grpLayer, xPos, yPos, width, height, color):
  # Create a background layer for the matching row
  bg_layer = Gimp.Layer.new(image, "Player Highlight", width, height, Gimp.ImageType.RGBA_IMAGE, 50, Gimp.LayerMode.NORMAL)
  image.insert_layer( bg_layer, grpLayer, -1 )
  bg_layer.set_offsets( xPos, yPos )

  # Set background color (red with 50% transparency)
  curFG = Gimp.context_get_foreground()
  green = Gimp.color_parse_hex( color )
  Gimp.context_set_foreground(green)  # Red, 50% alpha
  bg_layer.edit_fill(Gimp.FillType.FOREGROUND)
  Gimp.context_set_foreground(curFG)
  
def create_title_card(image, grpLayer, ptSize, font, value):
  text_layer = create_text_layer_at( image, value, font, ptSize * 2, grpLayer, 0, 100 )
  # Centre it
  lWidth = text_layer.get_width()
  iWidth = image.get_width()
  newX = (iWidth / 2) - (lWidth / 2)
  text_layer.set_offsets( newX, 100 )
  return text_layer

def process_table( parLayer, image, data, xPos, yPos, ptSize):

  white = Gimp.color_parse_hex( "FFFFFF" )
  Gimp.context_set_foreground(white)  # Red, 50% alpha
  offsets = [ptSize * 9, ptSize * 55, ptSize * 9, ptSize * 9, ptSize * 9, ptSize * 9, ptSize * 15, ptSize * 18, ptSize * 12, ptSize * 12, 200]
  fields = ["Rank", "Team", "GamesPlayed", "GamesWon", "GamesDrawn", "GamesLost", "GoalsFor",  "GoalsAgainst",  "Points", "GoalsDiff", "WinLoss"]
  labels = ["Pos",  "Team", "GP",          "W",        "D",          "L",         "GF",        "GA",            "Pts",    "GD",        "Last 5" ]
  x_offset = 200  # Horizontal spacing
  target_name = "Oxley United FC"  # Name to highlight

  div = data['div']
  table = data['table']
  # Find row index for the target name
  row_index = next((i for i, entry in enumerate(table) if entry["Team"] == target_name), None)
  
  font = Gimp.Font.get_by_name("Serif")
  # Loop through fields to create text layers
  runningOffset = x_offset
  grpLayer = Gimp.GroupLayer.new(image, div['name'] + " Table")
  image.insert_layer( grpLayer, parLayer, -1 )
  lHeight = 0
  create_title_card(image, grpLayer, ptSize, font, div['name'])
  for i, field in enumerate(fields):
    field_values = "\n".join( [labels[i]] + extract_column( table, field ) )
    text_layer = create_text_layer_at( image, field_values, font, ptSize, grpLayer, xPos + runningOffset, yPos )
    runningOffset += offsets[i]
    lHeight = text_layer.get_height()

  if row_index is not None:
    numRecords = len(table) + 1
    rowSlice = lHeight / numRecords
    rowOffset_y = rowSlice * (row_index + 1)
    rowBottom_y = rowSlice * (row_index + 2)
    create_highlight_row( image, grpLayer, xPos, yPos + rowOffset_y, runningOffset + (ptSize * 20), rowBottom_y - rowOffset_y)
  return image

def load_json(filename):
  try:
    with open(filename, "r", encoding="utf-8") as file:
      data = json.load(file)
      return data
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return []
  except json.JSONDecodeError:
    print("Error: Failed to decode JSON. Ensure the file contains valid JSON.")
    return []

def score_table_run(procedure, run_mode, image, drawables, config, data):

  # Read JSON
  chooser = JsonFileChooser( "Select JSON file with score tables" )
  json_path = chooser.run()
  if json_path:
    data = load_json( json_path )

    image.undo_group_start()
    grpLayer = Gimp.GroupLayer.new(image, "Tables")
    image.insert_layer( grpLayer, None, 0 )
    for i, entry in enumerate(data):
        process_table( grpLayer, image, entry, 200, 600, 28 )
    image.undo_group_end()

    return procedure.new_return_values( Gimp.PDBStatusType.SUCCESS, None )
  else:
    return procedure.new_return_values( Gimp.PDBStatusType.CANCEL, GLib.Error() )

def newDimensions( layer, newMaxDim ):
  
  yVal = layer.get_height()
  xVal = layer.get_width()
  if yVal > xVal:
    divisor = newMaxDim / yVal
    return [ xVal * divisor, newMaxDim]
    # Taller than wide
  else:
    # Wider than tall
    divisor = newMaxDim / xVal
    return [ newMaxDim, yVal * divisor]


def loadImageAsLayer( image, filename, offsetX, offsetY, parentLayer = None, maxDimension = 400 ):
  file = Gio.File.new_for_path( filename )
  hlayer = Gimp.file_load_layer( Gimp.RunMode.NONINTERACTIVE, image, file )
  image.insert_layer( hlayer, parentLayer, -1 )
  hX, hY = newDimensions( hlayer, maxDimension )
  hlayer.scale( hX, hY, True )
  hlayer.set_offsets( offsetX, offsetY )
  
def process_fixture_table(image, run_mode, folder, fixtures, ptSize ):

  font = Gimp.Font.get_by_name("Serif")
  # Loop through fields to create text layers
  grpLayer = Gimp.GroupLayer.new(image, "Fixtures")
  image.insert_layer( grpLayer, None, 0 )
  round_layer = create_title_card(image, grpLayer, ptSize * 2 / 3, font, "Upcoming fixtures" )
  _,xPos,_ = round_layer.get_offsets()
  round_layer.set_offsets( xPos, 675 )
  
  for i, entry in enumerate(fixtures):
    
    div = entry['div']
    match = entry['match']
    
    grpLayerTeam = Gimp.GroupLayer.new( image, div['name'] )
    image.insert_layer( grpLayerTeam, grpLayer, 0 )
    
    #
    # {
    #   "div": "Met 5s",
    #   "when": "Fri, Jun 20 06:30 PM",
    #   "home": "Annerley FC",
    #   "away": "Oxley United FC",
    #   "ground": "Elder Oval, Field 1"
    # },
    #
    text_value = div['name'] + " - " + match["when"] + "\n" + match["ground"] + " vs "
    if match["home"] != "Oxley United FC":
      text_value += match["home"]
    else:
      text_value += match["away"]
      
    create_text_layer_at( image, text_value, font, ptSize, grpLayerTeam, 1500, 1000 + i * 500 )

    # Load logos
    loadImageAsLayer( image, folder + "\\" + match["home"] + ".png", 500, 1000 + i * 500, grpLayerTeam, 400 )
    loadImageAsLayer( image, folder + "\\" + match["away"] + ".png", 5000, 1000 + i * 500, grpLayerTeam, 400 )

  return image

def process_fixture_results( image, run_mode, folder, fixtures, ptSize ):

  font = Gimp.Font.get_by_name("Serif")
  # Loop through fields to create text layers
  grpLayer = Gimp.GroupLayer.new(image, "Results")
  image.insert_layer( grpLayer, None, 0 )
  round_layer = create_title_card(image, grpLayer, ptSize * 2 / 3, font, "Latest Results" )
  _,xPos,_ = round_layer.get_offsets()
  round_layer.set_offsets( xPos, 675 )
  
  i = 0
  for entry in fixtures:
    
    div = entry['div']
    match = entry['match']
    
    grpLayerTeam = Gimp.GroupLayer.new( image, div['name'] )
    image.insert_layer( grpLayerTeam, grpLayer, 0 )
    
    create_text_layer_at( image, div['name'],             font, ptSize, grpLayerTeam, 100, 1100 + i * 500 )
    create_text_layer_at( image, match["home"],           font, ptSize, grpLayerTeam, 1500, 1100 + i * 500 )
    create_text_layer_at( image, str(match["goalsHome"]), font, ptSize, grpLayerTeam, 2850, 1100 + i * 500 )
    create_text_layer_at( image, str(match["goalsAway"]), font, ptSize, grpLayerTeam, 3150, 1100 + i * 500 )
    create_text_layer_at( image, match["away"],           font, ptSize, grpLayerTeam, 3500, 1100 + i * 500 )

    # Load home
    hlayer = create_image_layer_at( image, folder, match["home"], grpLayerTeam, 400, 1000, 1000 + i * 500 )
    alayer = create_image_layer_at( image, folder, match["away"], grpLayerTeam, 400, 5000, 1000 + i * 500 )
    
    if match["goalsHome"] < match["goalsAway"]:
      hlayer.desaturate(Gimp.DesaturateMode.LUMINANCE)
    elif match["goalsAway"] < match["goalsHome"]:
      alayer.desaturate(Gimp.DesaturateMode.LUMINANCE)
    i = i + 1
  return image

def process_team_fixture_table( image, folder, division, fixtures, ptSize ):

  font = Gimp.Font.get_by_name("Serif")
  # Loop through fields to create text layers
  grpLayer = Gimp.GroupLayer.new(image, "Fixtures " + division)
  image.insert_layer( grpLayer, None, 0 )
  div_layer = create_title_card(image, grpLayer, ptSize * 2 / 3, font, division)
  _,xPos,_ = div_layer.get_offsets()
  div_layer.set_offsets( xPos, 675 )
  
  i = 0
  for entry in fixtures:
    
    grpLayerTeam = Gimp.GroupLayer.new( image, "Round " + str(entry["round"]) )
    image.insert_layer( grpLayerTeam, grpLayer, 0 )
    
    #
    # {
    #   "round": "1",
    #   "when": "Fri, Jun 20 06:30 PM",
    #   "home": "Annerley FC",
    #   "away": "Oxley United FC",
    #   "ground": "Elder Oval, Field 1"
    # },
    #
    text_value = "Round " + str(entry["round"]) + " - " + entry["when"] + "\n" + entry["ground"] + " vs "
    if entry["home"] != "Oxley United FC":
      text_value += entry["home"]
    else:
      text_value += entry["away"]
      
    create_text_layer_at( image, text_value, font, ptSize, grpLayerTeam, 2000, 1000 + i * 500 )

    # Load home    
    file = Gio.File.new_for_path( folder + "\\" + entry["homeImage"] )
    hlayer = Gimp.file_load_layer(Gimp.RunMode.NONINTERACTIVE, image, file)
    image.insert_layer(hlayer, grpLayerTeam, -1 )
    hX, hY = newDimensions( hlayer, 400 )
    hlayer.scale( hX, hY, True )
    hlayer.set_offsets( 1500, 1000 + i * 500 )

    file = Gio.File.new_for_path( folder + "\\" + entry["awayImage"] )
    alayer = Gimp.file_load_layer(Gimp.RunMode.NONINTERACTIVE, image, file)
    image.insert_layer(alayer, grpLayerTeam, -1 )
    aX, aY = newDimensions( alayer, 400 )
    alayer.scale( aX, aY, True )
    alayer.set_offsets( 4500, 1000 + i * 500 )

    i = i + 1
  return image

def process_infographic(image, run_mode, folder, data, ptSize ):

  topSpot = 250
  firstLine = 1000
  lineHeight = 250
  secondLine = 2200
  
  font = Gimp.Font.get_by_name("Serif")
  # Loop through fields to create text layers
  grpLayer = Gimp.GroupLayer.new(image, "Infographic")
  image.insert_layer( grpLayer, None, 0 )
  title_layer = create_title_card(image, grpLayer, ptSize, font, "Stats so far" )
  _,xPos,_ = title_layer.get_offsets()
  title_layer.set_offsets( xPos, topSpot - 150 )
  
  ball   = "\U000026BD"
  person = "\U0001F464"  
  labels = [ "Total Goals", "Number of Scorers", "Top scorer", "Average Goals / Round", "Best Round" ]
  dataEntries = [
    str(data["goals"]) + " " + ball,
    str(data["uniqueScorers"]) + " " + person,
    data["top_scorer"]["name"] + " with " + str( data["top_scorer"]["goals"] ) + " goals",
    f"{data["avgGoalsPerRound"]:.2f}",
    str(data["highestRoundGoals"]) + " in round " + str( data["highestRound"] )
  ]

  create_text_layer_at( image, ball + " Goals " + ball, font, ptSize * 2, grpLayer,  200, topSpot + lineHeight )
  for i, label in enumerate(labels):
    create_text_layer_at( image, label,                 font, ptSize, grpLayer,  500, firstLine + i * lineHeight )
    create_text_layer_at( image, str( dataEntries[i] ), font, ptSize, grpLayer, 2850, firstLine + i * lineHeight )
  
  labels = [ "Total Cards", "Players Carded", "Top card holder" ]
  create_card( image, grpLayer, 300, secondLine + lineHeight, 200, 400 )
  create_text_layer_at( image, "Cards", font, ptSize * 2, grpLayer, 500, secondLine + lineHeight )
  create_card( image, grpLayer, 1500, secondLine + lineHeight, 200, 400 )
  dataEntries = [
    str(data["yellows"]),
    str(data["uniqueCarders"]) + " " + person,
    data["top_carder"]["name"] + " with " + str( data["top_carder"]["cards"] ) + " cards"
  ]
  for i, label in enumerate(labels):
    create_text_layer_at( image, label,                 font, ptSize, grpLayer,  500, secondLine + (i+3) * lineHeight )
    create_text_layer_at( image, str( dataEntries[i] ), font, ptSize, grpLayer, 2850, secondLine + (i+3) * lineHeight )
  
  return image

def getSpecificDetails( name, data, attr, label ):
  if name != 'overall':
    return data[attr]["name"] + " with " + str( data[attr]["value"] ) + " " + label
  else:
    return str( data[attr]["value"] )


def getDirection( value ):
  return (1 if value > 0 else (-1 if value < 0 else 0 ) )


def processStatLayer( image, label, value, direction, font, ptSize, grpLayer, x1, x2, y1, lineHeight ):
  create_text_layer_at( image, label,        font, ptSize, grpLayer, x1, y1 )
  create_text_layer_at( image, str( value ), font, ptSize, grpLayer, x2, y1 )
  dir, colUp, colDown = direction
  match dir:
    case -1:
      draw_chevron_down( image, x2 - lineHeight, y1, lineHeight * 0.6, lineHeight * 0.6, colDown )
    case 0:
      curFG = Gimp.context_get_foreground()
      Gimp.context_set_foreground( Gimp.color_parse_hex( "#FFBB40" ) )
      create_text_layer_at( image, "=", font, ptSize, grpLayer, 2650, y1 )
      Gimp.context_set_foreground( curFG )
    case 1:
      draw_chevron_up( image, x2 - lineHeight, y1, lineHeight * 0.6, lineHeight * 0.6, colUp )
  

def process_team_infographic( image, run_mode, folder, name, data, ptSize ):

  topSpot = 250
  firstLine = 1000
  lineHeight = 250
  secondLine = 2200
  
  font = Gimp.Font.get_by_name("Serif")
  # Loop through fields to create text layers
  grpLayer = Gimp.GroupLayer.new(image, name + " Infographic")
  image.insert_layer( grpLayer, None, 0 )
  title_layer = create_title_card(image, grpLayer, ptSize, font, name.capitalize() + " Stats" )
  _,xPos,_ = title_layer.get_offsets()
  title_layer.set_offsets( xPos, topSpot - 150 )
  
  ball    = "\U000026BD"
  person  = "\U0001F464"  
  good    = "#00FF00"
  bad     = "#FF0000"
  
  # Statistics
  labels  = [ "Players", "Goals", "Number of Scorers", "Top scorer", "Average Goals / Round", "Best Round" ]
  inRound = " in round " + str( data["highestRound"]) if name != 'overall' else ""
  dataEntries = [
    str(data["players"]) + " " + person,
    str(data["goals"]) + " " + ball,
    str(data["uniqueScorers"]) + " " + person,
    getSpecificDetails( name, data, 'top_scorer', 'goals' ),
    f"{data["avgGoalsPerRound"]:.2f}",
    str(data["highestRoundGoals"]) + inRound
  ]
  direction = [
    ( getDirection( data['players']  ), good, bad ),
    ( getDirection( data['goals']  ), good, bad ),
    ( getDirection( data['uniqueScorers']  ), good, bad ),
    ( getDirection( data["top_scorer"]["value"]  ), good, bad ),
    ( getDirection( data['avgGoalsPerRound']  ), good, bad ),
    ( getDirection( data['highestRoundGoals']  ), good, bad ),
  ]
  create_text_layer_at( image, ball + " Goals " + ball, font, ptSize * 2, grpLayer,  200, topSpot + lineHeight )
  for i, label in enumerate(labels):
    processStatLayer( image, label, dataEntries[i], direction[i], font, ptSize, grpLayer, 500, 2850, firstLine + i * lineHeight, lineHeight )

  # FIFA Fair Play
  labels = [ "Yellows", "Reds", "Players Carded", "Top card holder" ]
  create_card( image, grpLayer, 300, secondLine + lineHeight + 100, 200, 300 )
  create_text_layer_at( image, "Cards", font, ptSize * 2, grpLayer, 500, secondLine + lineHeight )
  create_card( image, grpLayer, 1500, secondLine + lineHeight + 100, 200, 300, color="#FF0000" )
  dataEntries = [
    str(data["yellows"]),
    str(data["reds"]),
    str(data["uniqueCarders"]) + " " + person,
    getSpecificDetails( name, data, 'top_carder', 'value' ),
  ]
  direction = [
    ( getDirection( data['yellows']  ), bad, good ),
    ( getDirection( data['reds']  ), bad, good ),
    ( getDirection( data['uniqueCarders']  ), bad, good ),
    ( getDirection( data["top_carder"]["value"]  ), bad, good ),
  ]
  for i, label in enumerate(labels):
    processStatLayer( image, label, dataEntries[i], direction[i], font, ptSize, grpLayer, 500, 2850, secondLine + (i+3) * lineHeight, lineHeight )

  # Matches
  labels = [ "Wins", "Draws", "Losses", "Goals For", "Goals Against", "Rank" ]
  create_text_layer_at( image, "Matches", font, ptSize * 2, grpLayer,  3600, topSpot + lineHeight )
  dataEntries = [ str( data['teams']["wins"] ), str( data['teams']["draws"] ), str( data['teams']["losses"] ),
                  str( data['teams']["gf"] ),   str( data['teams']["ga"] ),    f"{data['teams']["avgRank"]:.2f}"
  ]
  direction = [
    ( getDirection( data['teams']['wins']  ), good, bad ),
    ( getDirection( data['teams']['draws']  ), good, bad ),
    ( getDirection( data['teams']['losses']  ), bad, good ),
    ( getDirection( data['teams']["gf"]  ), good, bad ),
    ( getDirection( data['teams']['ga']  ), bad, good ),
    ( getDirection( data['teams']['avgRank']  ), bad, good ),
  ]
  for i, label in enumerate(labels):
    processStatLayer( image, label, dataEntries[i], direction[i], font, ptSize, grpLayer, 3600, 5000, firstLine + i * lineHeight, lineHeight )
  
  return image

def fixture_run( procedure, run_mode, image, drawables, config, data ):

  # Read JSON
  chooser = JsonFileChooser( "Select JSON file with fixtures" )
  json_path = chooser.run()
  if json_path:
    fixData = load_json( json_path )
    
    logoFolder = "D:\\Media\\Oxley\\ClubLogos"

    image.undo_group_start()
    process_fixture_table( image, run_mode, logoFolder, fixData, 32 )
    image.undo_group_end()

    return procedure.new_return_values( Gimp.PDBStatusType.SUCCESS, None )
  else:
    return procedure.new_return_values( Gimp.PDBStatusType.CANCEL, GLib.Error() )

def fixture_res_run(procedure, run_mode, image, drawables, config, data):

  # Read JSON
  chooser = JsonFileChooser( "Select JSON file with results" )
  json_path = chooser.run()
  if json_path:
    fixData = load_json( json_path )
    
    logoFolder = "D:\\Media\\Oxley\\ClubLogos"

    fixtures = [ entry for entry in fixData if (entry['match']['home'] != 'Bye' and entry['match']['away'] != 'Bye') ]

    image.undo_group_start()
    process_fixture_results( image, run_mode, logoFolder, fixtures, 32 )
    image.undo_group_end()

    return procedure.new_return_values( Gimp.PDBStatusType.SUCCESS, None )
  else:
    return procedure.new_return_values( Gimp.PDBStatusType.CANCEL, GLib.Error() )

def team_fixture_run(procedure, run_mode, image, drawables, config, data):

  # Read JSON
  fixData = load_json("D:\\Media\\Oxley\\squadi\\team_fixtures.json")
  logoFolder = "D:\\Media\\Oxley\\ClubLogos"

  image.undo_group_start()
  for i, entry in enumerate(fixData):
    division = entry["div"]
    fixtures = entry["fixtures"]
    print( "Processing division " + division )
    process_team_fixture_table( image, logoFolder, division, fixtures, 32 )
  image.undo_group_end()

  return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)

def draw_hexagon( layer, xOff, yOff, size ):

  tL = [xOff - size / 4, yOff + size / 2]
  mL = [xOff - size / 2, yOff]
  bL = [xOff - size / 4, yOff - size / 2]
  tR = [xOff + size / 4, yOff + size / 2]
  mR = [xOff + size / 2, yOff]
  bR = [xOff + size / 4, yOff - size / 2]
  
  linecoords = [ tL[0], tL[1], tR[0], tR[1], mR[0], mR[1], bR[0], bR[1], bL[0], bL[1], mL[0], mL[1], tL[0], tL[1] ]
  Gimp.pencil( layer, linecoords )

def draw_shape_run(procedure, run_mode, image, drawables, config, data):

  image.undo_group_start()

  brushSize   = 10
  orgLineWith = Gimp.context_get_brush_size()
  Gimp.context_set_brush_size( brushSize )
  curFG = Gimp.context_get_foreground()
  newFG = Gimp.color_parse_hex( "000000" )
  
  drawLayer = Gimp.Layer.new(image, "Texture", image.get_width(), image.get_height(), Gimp.ImageType.RGBA_IMAGE, 100, Gimp.LayerMode.NORMAL)
  image.insert_layer( drawLayer, None, 0 )
  Gimp.context_set_foreground( newFG )
  
  size = 256
  cX = 1024
  cY = 1024
  oddIncX = (2 * size) - (size / 2)
  evnIncX = (3 * size) / 4
  evnIncY = (2 * size) - (size / 2)

  for i in range(7):
    thisX = cX + (i - 3) * oddIncX
    nextX = cX + (i - 2) * oddIncX
    prevX = cX + (i - 4) * oddIncX
    thisOX = thisX + evnIncX
    nextOX = nextX + evnIncX
    prevOX = prevX + evnIncX
    draw_hexagon( drawLayer, thisX,  cY + 2 * evnIncY, size )
    draw_hexagon( drawLayer, thisOX, cY + 1 * evnIncY, size )
    draw_hexagon( drawLayer, thisX,  cY + 0 * evnIncY, size )
    draw_hexagon( drawLayer, thisOX, cY - 1 * evnIncY, size )
    draw_hexagon( drawLayer, thisX,  cY - 2 * evnIncY, size )
    # Now we have to fill some lines in ...

    # Horizontal lines
    Gimp.pencil( drawLayer, [  thisX + size / 2, cY + 2 * evnIncY,  nextX - size / 2, cY + 2 * evnIncY ] )
    Gimp.pencil( drawLayer, [ thisOX + size / 2, cY + 1 * evnIncY, nextOX - size / 2, cY + 1 * evnIncY ] )
    Gimp.pencil( drawLayer, [  thisX + size / 2, cY + 0 * evnIncY,  nextX - size / 2, cY + 0 * evnIncY ] )
    Gimp.pencil( drawLayer, [ thisOX + size / 2, cY - 1 * evnIncY, nextOX - size / 2, cY - 1 * evnIncY ] )
    Gimp.pencil( drawLayer, [  thisX + size / 2, cY - 2 * evnIncY,  nextX - size / 2, cY - 2 * evnIncY ] )
    
    # Diagonal lines
    # BR -> TL
    Gimp.pencil( drawLayer, [  thisX + size / 4, cY + size / 2 + 2 * evnIncY, thisOX - size / 4, cY + 3 * evnIncY - size / 2 ] )
    Gimp.pencil( drawLayer, [  thisX + size / 4, cY + size / 2 + 0 * evnIncY, thisOX - size / 4, cY + 1 * evnIncY - size / 2 ] )
    Gimp.pencil( drawLayer, [  thisX + size / 4, cY + size / 2 - 2 * evnIncY, thisOX - size / 4, cY - 1 * evnIncY - size / 2 ] )
    # BL -> TR
    Gimp.pencil( drawLayer, [  thisX - size / 4, cY + size / 2 + 2 * evnIncY, prevOX + size / 4, cY + 3 * evnIncY - size / 2 ] )
    Gimp.pencil( drawLayer, [  thisX - size / 4, cY + size / 2 + 0 * evnIncY, prevOX + size / 4, cY + 1 * evnIncY - size / 2 ] )
    Gimp.pencil( drawLayer, [  thisX - size / 4, cY + size / 2 - 2 * evnIncY, prevOX + size / 4, cY - 1 * evnIncY - size / 2 ] )
    # TR -> BL
    Gimp.pencil( drawLayer, [  thisX + size / 4, cY - size / 2 + 2 * evnIncY, thisOX - size / 4, cY + 1 * evnIncY + size / 2 ] )
    Gimp.pencil( drawLayer, [  thisX + size / 4, cY - size / 2 + 0 * evnIncY, thisOX - size / 4, cY - 1 * evnIncY + size / 2 ] )
    Gimp.pencil( drawLayer, [  thisX + size / 4, cY - size / 2 - 2 * evnIncY, thisOX - size / 4, cY - 3 * evnIncY + size / 2 ] )
    # TL -> BR
    Gimp.pencil( drawLayer, [  thisX - size / 4, cY - size / 2 + 2 * evnIncY, prevOX + size / 4, cY + 1 * evnIncY + size / 2 ] )
    Gimp.pencil( drawLayer, [  thisX - size / 4, cY - size / 2 + 0 * evnIncY, prevOX + size / 4, cY - 1 * evnIncY + size / 2 ] )
    Gimp.pencil( drawLayer, [  thisX - size / 4, cY - size / 2 - 2 * evnIncY, prevOX + size / 4, cY - 3 * evnIncY + size / 2 ] )

  Gimp.context_set_brush_size( orgLineWith )
  Gimp.context_set_foreground( curFG )
  image.undo_group_end()

  return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)

def infographic_run(procedure, run_mode, image, drawables, config, data):

  # Read JSON
  chooser = JsonFileChooser( "Select JSON file with infographic details" )
  json_path = chooser.run()
  if json_path:
    infoData = load_json( json_path )
    
    logoFolder = "D:\\Media\\Oxley\\ClubLogos"

    image.undo_group_start()
    process_infographic( image, run_mode, logoFolder, infoData, 48 )
    image.undo_group_end()

    return procedure.new_return_values( Gimp.PDBStatusType.SUCCESS, None )
  else:
    return procedure.new_return_values( Gimp.PDBStatusType.CANCEL, GLib.Error() )


def team_info_run(procedure, run_mode, image, drawables, config, data):

  # Read JSON
  chooser = JsonFileChooser( "Select JSON file with team infographic details" )
  json_path = chooser.run()
  if json_path:
    infoData = load_json( json_path )
    
    logoFolder = "D:\\Media\\Oxley\\ClubLogos"

    image.undo_group_start()
    for name, stats in infoData.items():
      process_team_infographic( image, run_mode, logoFolder, name, stats, 48 )
      break
    image.undo_group_end()

    return procedure.new_return_values( Gimp.PDBStatusType.SUCCESS, None )
  else:
    return procedure.new_return_values( Gimp.PDBStatusType.CANCEL, GLib.Error() )


def chevron_run( procedure, run_mode, image, drawables, config, data ):
  image.undo_group_start()
  points = chevron_up( x=3000, y=2000, height=400, width=400 )
  neon_gradient_fill( image=image,
                      points=points,
                      color1="#00FF40",   # lime
                      color2="#0080FF",   # emerald
                      glow_px=40,
                      feather_px=20,
                      name="neon_up"
    )
  #points = chevron_down( x=3000, y=2000, height=400, width=150 )
  #neon_gradient_fill( image=image,
  #                    points=points,
  #                    color1="#0040FF",   # lime
  #                    color2="#0080FF",   # emerald
  #                    glow_px=40,
  #                    feather_px=20,
  #                    name="neon_up"
  #  )
  image.undo_group_end()
  return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)
  


class SoccerPlugin (Gimp.PlugIn):
  def do_query_procedures(self):
    print( "Query self procedures" )
    return [ score_table_proc, next_fixture_prc, team_fixture_prc, draw_football_pr, fixture_res_proc, infographic_proc, chevron_proc, team_info_proc ]

  def do_set_i18n (self, name):
      return False

  def do_create_procedure(self, name):
    procedure = None

    if name == score_table_proc:
      procedure = self.createProc(name, score_table_run, "Score Tables", '<Image>/Filters/Soccer/', "Score Tables" )
      
    if name == next_fixture_prc:
      procedure = self.createProc(name, fixture_run, "Layout fixtures", '<Image>/Filters/Soccer/', "Layout Fixtures" )
      
    if name == team_fixture_prc:
      procedure = self.createProc(name, team_fixture_run, "Team fixtures", '<Image>/Filters/Soccer/', "Team Fixtures" )
      
    if name == draw_football_pr:
      procedure = self.createProc(name, draw_shape_run, "Draw Football shape", '<Image>/Filters/Soccer/', "Draw Football" )
      
    if name == fixture_res_proc:
      procedure = self.createProc(name, fixture_res_run, "Display Fixture Results", '<Image>/Filters/Soccer/', "Display Fixture Results" )
      
    if name == infographic_proc:
      procedure = self.createProc(name, infographic_run, "Create Infographic", '<Image>/Filters/Soccer/', "Create Infographic" )
      
    if name == chevron_proc:
      procedure = self.createProc( name, chevron_run, "Create Chevron", '<Image>/Filters/Soccer/', "Create Chevron" )
      
    if name == team_info_proc:
      procedure = self.createProc( name, team_info_run, "Team Infographic", '<Image>/Filters/Soccer/', "Team Infographic" )
      
    return procedure

  def createProc(self, name, func, menuLabel, menuPath, documentation):
      procedure = Gimp.ImageProcedure.new( self, name, Gimp.PDBProcType.PLUGIN, func, None)
      procedure.set_sensitivity_mask (Gimp.ProcedureSensitivityMask.DRAWABLE | Gimp.ProcedureSensitivityMask.NO_DRAWABLES)
      procedure.set_menu_label(menuLabel)
      procedure.set_attribution("Daniel Stratton", "Daniel Stratton", "2026")
      procedure.add_menu_path(menuPath)
      procedure.set_documentation( documentation, documentation, None )
      return procedure

Gimp.main(SoccerPlugin.__gtype__, sys.argv)