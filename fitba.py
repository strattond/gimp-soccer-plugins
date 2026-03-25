#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
from gi.repository import Gimp, Gio, GimpUi, GLib, Gtk

import sys
import json
import math

score_table_proc  = "plug-in-football-tables"
golden_boot_proc  = "plug-in-football-golden-boot"
next_fixture_prc  = "plug-in-football-fixture"
team_fixture_prc  = "plug-in-football-fixture-team"
draw_football_pr  = "plug-in-football-shape"
fixture_res_proc  = "plug-in-football-results"

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
    return
  return [str(record[attr]) for record in data]

def coords_to_vec2_list(flat_coords):
  return [(flat_coords[i], flat_coords[i + 1]) for i in range(0, len(flat_coords), 2)]

  
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

  # Find row index for the target name
  row_index = next((i for i, entry in enumerate(data["table"]) if entry["Team"] == target_name), None)
  print(row_index)
  
  font = Gimp.Font.get_by_name("Serif")
  # Loop through fields to create text layers
  runningOffset = x_offset
  grpLayer = Gimp.GroupLayer.new(image, data["comp"] + " Table")
  image.insert_layer( grpLayer, parLayer, -1 )
  lHeight = 0
  create_title_card(image, grpLayer, ptSize, font, data["comp"])
  for i, field in enumerate(fields):
    field_values = "\n".join( [labels[i]] + extract_column( data["table"], field ) )
    text_layer = create_text_layer_at( image, field_values, font, ptSize, grpLayer, xPos + runningOffset, yPos )
    runningOffset += offsets[i]
    lHeight = text_layer.get_height()

  if row_index is not None:
    numRecords = len(data["table"]) + 1
    rowSlice = lHeight / numRecords
    rowOffset_y = rowSlice * (row_index + 1)
    rowBottom_y = rowSlice * (row_index + 2)
    create_highlight_row( image, grpLayer, xPos, yPos + rowOffset_y, runningOffset + (ptSize * 20), rowBottom_y - rowOffset_y)
  return image

def process_gb_table(image, data, xPos, yPos, ptSize):

  nPlayers = len(data)
  firstE = data[0]
  nRounds = len(firstE["scores"])
  offsets = [None] * (nRounds + 1)
  labels  = [None] * (nRounds + 1)
  labels[0] = 'Player'
  offsets[0] = 1000
  for i in range(nRounds):
    labels[i + 1] = str(i + 1)
    offsets[i + 1] = 250
  runningOffset = 200
  font = Gimp.Font.get_by_name("Serif")
  # Loop through fields to create text layers
  grpLayer = Gimp.GroupLayer.new(image, "Golden Boot Table")
  image.insert_layer( grpLayer, None, 0 )
  create_title_card(image, grpLayer, ptSize, font, "Metro Golden Boot")
  name_values = "\n".join( [labels[0]] + extract_column( data, "name" ) )
  text_layer = create_text_layer_at( image, name_values, font, ptSize, grpLayer, xPos + runningOffset, yPos )
  runningOffset += offsets[0]
  
  round_layer = create_title_card(image, grpLayer, ptSize / 2, font, "Match")
  round_layer.set_offsets( xPos + runningOffset, yPos - round_layer.get_height())
  
  for i in range(nRounds):
    nth_scores = [str(entry["scores"][i]) for entry in data if i < len(entry["scores"])]
    nth_totals = [str(entry["running_total"][i]) for entry in data if i < len(entry["running_total"])]
    field_values = labels[i + 1] + "\n"
    for j in range(len(nth_scores)):
      #field_values += nth_scores[j] + " (" + nth_totals[j] + ")\n"
      #field_values += nth_scores[j] + "\n"
      if nth_scores[j] != '0':
        field_values += nth_scores[j] + "\n"
      else:
        field_values += "\n"
        
    text_layer = create_text_layer_at( image, field_values, font, ptSize, grpLayer, xPos + runningOffset, yPos )
    runningOffset += offsets[i+1]

  colors = [ "FF0000", "00FF00", "0000FF", "FFFF00", "FF00FF"]
  name_height = (text_layer.get_height() - 100) / (nPlayers+1)
  for i in range(nPlayers):
    create_player_colour( image, grpLayer, 200, yPos + (name_height) * (i+1), 100, 100, colors[i] )

  drawLayer = Gimp.Layer.new(image, "Golden Boot Graph Drawing", image.get_width(), image.get_height(), Gimp.ImageType.RGBA_IMAGE, 100, Gimp.LayerMode.NORMAL)
  image.insert_layer( drawLayer, grpLayer, -1 )

  orgLineWith = Gimp.context_get_brush_size()
  brushSize = 15
  Gimp.context_set_brush_size( brushSize )
  Gimp.pencil( drawLayer, [xPos, yPos + name_height - 25, xPos + runningOffset, yPos + name_height - 25])
  Gimp.pencil( drawLayer, [xPos + 1100, yPos, xPos + 1100, yPos + text_layer.get_height() - name_height] )
  Gimp.context_set_brush_size( orgLineWith )
    
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

def draw_gb_graph(image, data, xPos, yPos, ptSize):
  
  graphHeight = 2000
  brushSize   = 30
  firstE      = data[0]
  nRounds     = len(firstE["scores"])
  bottom      = yPos + graphHeight
  rightH      = image.get_width() - xPos
  tickX       = (rightH - xPos) / (nRounds + 1)
  nGoals      = firstE["goals"]
  font        = Gimp.Font.get_by_name("Serif")
  
  orgLineWith = Gimp.context_get_brush_size()
  Gimp.context_set_brush_size( brushSize )
  grpLayer = Gimp.GroupLayer.new(image, "Golden Boot Graph")
  image.insert_layer( grpLayer, None, 0 )
  drawLayer = Gimp.Layer.new(image, "Golden Boot Graph Drawing", image.get_width(), image.get_height(), Gimp.ImageType.RGBA_IMAGE, 100, Gimp.LayerMode.NORMAL)
  image.insert_layer( drawLayer, grpLayer, -1 )
  
  # Axis
  Gimp.pencil( drawLayer, [xPos, yPos, xPos, bottom, rightH, bottom])
  # X-Axis Ticks
  for i in range(nRounds):
    nextX = xPos + ( (i + 1) * tickX)
    Gimp.pencil( drawLayer, [nextX, bottom, nextX, bottom - 100])
  # Y-Axis ticks
  tickY = graphHeight / (nGoals+1)
  for i in range(nGoals):
    nextY = yPos + ((i + 1) * tickY)
    Gimp.pencil( drawLayer, [xPos, nextY, xPos + 100, nextY])
  # Y-Axis Labels
  for i in range(nGoals):
    nextY = yPos + ((i + 1) * tickY)
    label_value = str(nGoals - i)
    text_layer = create_text_layer_at( image, label_value, font, ptSize, grpLayer, 250, nextY - text_layer.get_height() / 2 )
    
  # X-Axis Labels
  for i in range(nRounds):
    nextX = xPos + ( (i + 1) * tickX)
    label_value = str(i + 1)
    text_layer = create_text_layer_at( image, label_value, font, ptSize, grpLayer, nextX - text_layer.get_width() / 2, bottom + 50 )
    
  # Player Graph
  curFG = Gimp.context_get_foreground()
  colors = [ "FF0000", "00FF00", "0000FF", "FFFF00", "FF00FF"]
  nPlayers = len(data)
  for i in range(nPlayers, 0, -1):
    # Per player, lowest first, so higher scored players "overlay" lower ones
    entry = data[i - 1]
    bl = [xPos, bottom]
    newFG = Gimp.color_parse_hex( colors[i - 1] )
   # Bottom left to round 1 cumulative, round 1 cumulative to round 2 cumulative, etc
    linecoords = [bl[0], bl[1]]
    for j in range(nRounds):
      goal = (entry["running_total"])[j]
      linecoords.append( xPos + (j + 1) * tickX)
      offset = (brushSize/2) * (nPlayers - (i+1))
      gOffset = goal * tickY
      linecoords.append( bottom - (gOffset + offset))
    
    print(linecoords)
    Gimp.context_set_foreground( newFG )
    Gimp.airbrush( drawLayer, 50, linecoords )
  
  Gimp.context_set_brush_size( orgLineWith )
  Gimp.context_set_foreground( curFG )

  return image

def golden_boot_run(procedure, run_mode, image, drawables, config, data):

  # Read JSON
  data = load_json("D:\\Media\\Oxley\\squadi\\goldenboot.json")
  
  for entry in data:
    entry["goals"] = sum(entry["scores"])
    entry["running_total"] = []
    temp_sum = 0
    for score in entry["scores"]:
      temp_sum += score
      entry["running_total"].append(temp_sum)
  
  sorted_data = sorted( data, key=lambda x: (-x["goals"], x["name"]) )
  
  top5 = sorted_data[:5]
  print( top5 )

  image.undo_group_start()
  process_gb_table( image, top5, 200, 600, 28 )
  draw_gb_graph( image, top5, 400, 1800, 28 )
  image.undo_group_end()

  return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)

def newDimensions(layer, newMaxDim):
  
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

def process_fixture_table(image, run_mode, folder, round, fixtures, ptSize ):

  nRounds = len(fixtures)
  font = Gimp.Font.get_by_name("Serif")
  # Loop through fields to create text layers
  grpLayer = Gimp.GroupLayer.new(image, "Fixtures")
  image.insert_layer( grpLayer, None, 0 )
  round_layer = create_title_card(image, grpLayer, ptSize * 2 / 3, font, "Round " + str(round))
  _,xPos,_ = round_layer.get_offsets()
  round_layer.set_offsets( xPos, 675 )
  
  i = 0
  for entry in fixtures:
    
    grpLayerTeam = Gimp.GroupLayer.new( image, entry["div"] )
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
    text_value = entry["div"] + " - " + entry["when"] + "\n" + entry["ground"] + " vs "
    if entry["home"] != "Oxley United FC":
      text_value += entry["home"]
    else:
      text_value += entry["away"]
      
    text_layer = create_text_layer_at( image, text_value, font, ptSize, grpLayerTeam, 2000, 1000 + i * 500 )

    # Load home    
    file = Gio.File.new_for_path( folder + "\\" + entry["home"] + ".png" )
    hlayer = Gimp.file_load_layer(Gimp.RunMode.NONINTERACTIVE, image, file)
    image.insert_layer(hlayer, grpLayerTeam, -1 )
    hX, hY = newDimensions( hlayer, 400 )
    hlayer.scale( hX, hY, True )
    hlayer.set_offsets( 1500, 1000 + i * 500 )

    file = Gio.File.new_for_path( folder + "\\" + entry["away"] + ".png" )
    alayer = Gimp.file_load_layer(Gimp.RunMode.NONINTERACTIVE, image, file)
    image.insert_layer(alayer, grpLayerTeam, -1 )
    aX, aY = newDimensions( alayer, 400 )
    alayer.scale( hX, hY, True )
    alayer.set_offsets( 4500, 1000 + i * 500 )


    i = i + 1
  return image

def process_fixture_results(image, run_mode, folder, round, fixtures, ptSize ):

  nRounds = len(fixtures)
  font = Gimp.Font.get_by_name("Serif")
  # Loop through fields to create text layers
  grpLayer = Gimp.GroupLayer.new(image, "Results")
  image.insert_layer( grpLayer, None, 0 )
  round_layer = create_title_card(image, grpLayer, ptSize * 2 / 3, font, "Round " + str(round))
  _,xPos,_ = round_layer.get_offsets()
  round_layer.set_offsets( xPos, 675 )
  
  i = 0
  for entry in fixtures:
    
    grpLayerTeam = Gimp.GroupLayer.new( image, entry["div"] )
    image.insert_layer( grpLayerTeam, grpLayer, 0 )
    
    create_text_layer_at( image, entry["div"],            font, ptSize, grpLayerTeam, 500, 1100 + i * 500 )
    create_text_layer_at( image, entry["home"],           font, ptSize, grpLayerTeam, 1500, 1100 + i * 500 )
    create_text_layer_at( image, str(entry["goalsHome"]), font, ptSize, grpLayerTeam, 2850, 1100 + i * 500 )
    create_text_layer_at( image, str(entry["goalsAway"]), font, ptSize, grpLayerTeam, 3150, 1100 + i * 500 )
    create_text_layer_at( image, entry["away"],           font, ptSize, grpLayerTeam, 3500, 1100 + i * 500 )

    # Load home
    hlayer = create_image_layer_at( image, folder, entry["home"], grpLayerTeam, 400, 1000, 1000 + i * 500 )
    alayer = create_image_layer_at( image, folder, entry["away"], grpLayerTeam, 400, 5000, 1000 + i * 500 )
    
    if entry["goalsHome"] < entry["goalsAway"]:
      hlayer.desaturate(Gimp.DesaturateMode.LUMINANCE)
    elif entry["goalsAway"] < entry["goalsHome"]:
      alayer.desaturate(Gimp.DesaturateMode.LUMINANCE)
    i = i + 1
  return image

def process_team_fixture_table(image, folder, division, fixtures, ptSize ):

  nRounds = len(fixtures)
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
      
    text_layer = create_text_layer_at( image, text_value, font, ptSize, grpLayerTeam, 2000, 1000 + i * 500 )

    # Load home    
    file = Gio.File.new_for_path( folder + "\\" + entry["homeImage"] )
    hlayer = Gimp.file_load_layer(Gimp.RunMode.NONINTERACTIVE, image, file)
    image.insert_layer(hlayer, grpLayerTeam, -1 )
    hX, hY = newDimensions( hlayer, 400 )
    #hlayer.resize( hX, hY, 0, 0 )
    hlayer.scale( hX, hY, True )
    hlayer.set_offsets( 1500, 1000 + i * 500 )

    file = Gio.File.new_for_path( folder + "\\" + entry["awayImage"] )
    alayer = Gimp.file_load_layer(Gimp.RunMode.NONINTERACTIVE, image, file)
    image.insert_layer(alayer, grpLayerTeam, -1 )
    aX, aY = newDimensions( alayer, 400 )
    #alayer.resize( aX, aY, 0, 0 )
    alayer.scale( hX, hY, True )
    alayer.set_offsets( 4500, 1000 + i * 500 )

    i = i + 1
  return image

def fixture_run(procedure, run_mode, image, drawables, config, data):

  # Read JSON
  chooser = JsonFileChooser( "Select JSON file with score tables" )
  json_path = chooser.run()
  if json_path:
    fixData = load_json( json_path )
    
    logoFolder = "D:\\Media\\Oxley\\ClubLogos"
    round = fixData["round"]
    fixtures = fixData["fixtures"]

    image.undo_group_start()
    process_fixture_table( image, run_mode, logoFolder, round, fixtures, 32 )
    image.undo_group_end()

    return procedure.new_return_values( Gimp.PDBStatusType.SUCCESS, None )
  else:
    return procedure.new_return_values( Gimp.PDBStatusType.CANCEL, GLib.Error() )

def fixture_res_run(procedure, run_mode, image, drawables, config, data):

  # Read JSON
  chooser = JsonFileChooser( "Select JSON file with score tables" )
  json_path = chooser.run()
  if json_path:
    fixData = load_json( json_path )
    
    logoFolder = "D:\\Media\\Oxley\\ClubLogos"
    round = fixData["round"]
    results = fixData["results"]

    image.undo_group_start()
    process_fixture_results( image, run_mode, logoFolder, round, results, 32 )
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

  return None

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
  oddIncY = 0
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

class SoccerPlugin (Gimp.PlugIn):
  def do_query_procedures(self):
    print( "Query self procedures" )
    return [ score_table_proc, golden_boot_proc, next_fixture_prc, team_fixture_prc, draw_football_pr, fixture_res_proc ]

  def do_set_i18n (self, name):
      return False

  def do_create_procedure(self, name):
    procedure = None

    if name == score_table_proc:
      procedure = self.createProc(name, score_table_run, "Score Tables", '<Image>/Filters/Soccer/', "Score Tables" )
      
    if name == golden_boot_proc:
      procedure = self.createProc(name, golden_boot_run, "Golden Boot", '<Image>/Filters/Soccer/', "Golden Boot" )
      
    if name == next_fixture_prc:
      procedure = self.createProc(name, fixture_run, "Layout fixtures", '<Image>/Filters/Soccer/', "Layout Fixtures" )
      
    if name == team_fixture_prc:
      procedure = self.createProc(name, team_fixture_run, "Team fixtures", '<Image>/Filters/Soccer/', "Team Fixtures" )
      
    if name == draw_football_pr:
      procedure = self.createProc(name, draw_shape_run, "Draw Football shape", '<Image>/Filters/Soccer/', "Draw Football" )
      
    if name == fixture_res_proc:
      procedure = self.createProc(name, fixture_res_run, "Display Fixture Results", '<Image>/Filters/Soccer/', "Display Fixture Results" )
      
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