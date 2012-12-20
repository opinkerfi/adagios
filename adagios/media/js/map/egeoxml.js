
/*********************************************************************\
*                                                                     *
* egeoxml.js                                         by Mike Williams *
*                                                                     *
* A Google Maps API Extension                                         *
*                                                                     *
* Renders the contents of a My Maps (or similar) KML file             *
*                                                                     *
* Documentation: http://econym.org.uk/gmap/egeoxml.htm                * 
*                                                                     *
***********************************************************************
*                                                                     *
*   This Javascript is provided by Mike Williams                      *
*   Community Church Javascript Team                                  *
*   http://www.bisphamchurch.org.uk/                                  *
*   http://econym.org.uk/gmap/                                        *
*                                                                     *
*   This work is licenced under a Creative Commons Licence            *
*   http://creativecommons.org/licenses/by/2.0/uk/                    *
*                                                                     *
\*********************************************************************/


// Version 0.0   17 Apr 2007 - Initial testing, just markers
// Version 0.1   17 Apr 2007 - Sensible shadows, and a few general improvements
// Version 0.2   18 Apr 2007 - Polylines (non-clickable, no sidebar)
// Version 0.3   18 Apr 2007 - Polygons (non-clickable, no sidebar)
// Version 0.4   18 Apr 2007 - Sidebar entries for polygons
// Version 0.5   19 Apr 2007 - Accept an array of XML filenames, and add the {sortbyname} option
// Version 0.6   19 Apr 2007 - Sidebar entries for polylines, get directions and search nearby
// Version 0.7   20 Apr 2007 - Info Window Styles
// Version 0.8   21 Apr 2007 - baseicon
// Version 0.9   21 Apr 2007 - iwoptions and markeroptions
// Version 1.0   21 Apr 2007 - Launched
// Version 1.1   25 Apr 2007 - Bugfix - would crash if no options were specified
// Version 1.2   25 Apr 2007 - If the description begins with "http://" make it into a link.
// Version 1.3   30 Apr 2007 - printgif, dropbox
// Version 1.4   14 May 2007 - Elabels
// Version 1.5   17 May 2007 - Default values for width, fill and outline
// Version 1.6   21 May 2007 - GGroundOverlay (needs API V2.79+)
// Version 1.7   22 May 2007 - Better icon positioning for MyMaps icons
// Version 1.8   31 May 2007 - polyline bugfix
// Version 1.9   23 Jun 2007 - add .parseString() method
// Version 2.0   23 Jun 2007 - .parseString() handles an array of strings
// Version 2.1   25 Jul 2007 - imagescan
// Version 2.2   10 Aug 2007 - Support new My Maps icons
// Version 2.3   25 Nov 2007 - Clear variables used by .parse() so that it can be rerun
// Version 2.4   08 Dec 2007 - polylineoptions and polygonoptions
// Version 2.5   11 Dec 2007 - EGeoXml.value() trims leading and trailing whitespace 
// Version 2.6   08 Feb 2008 - Trailing whitespace wasn't removed in the previous change
// Version 2.7   14 Oct 2008 - If there's no <description> try looking for <text> instead
// Version 2.8   12 Jan 2009 - Bugfix - last point of poly was omitted
// Version 2.9   05 Feb 2009 - add .hide() .show()

// Constructor

function EGeoXml(myvar, map, url, opts) {
  // store the parameters
  this.myvar = myvar;
  this.map = map;
  this.url = url;
  if (typeof url == "string") {
    this.urls = [url];
  } else {
    this.urls = url;
  }
  this.opts = opts || {};
  // infowindow styles
  this.titlestyle = this.opts.titlestyle || 'style = "font-family: arial, sans-serif;font-size: medium;font-weight:bold;font-size: 100%;"';
  this.descstyle = this.opts.descstyle || 'style = "font-family: arial, sans-serif;font-size: small;padding-bottom:.7em;"';
  this.directionstyle = this.opts.directionstyle || 'style="font-family: arial, sans-serif;font-size: small;padding-left: 1px;padding-top: 1px;padding-right: 4px;"';
  // sidebar/dropbox functions
  this.sidebarfn = this.opts.sidebarfn || EGeoXml.addSidebar;
  this.dropboxfn = this.opts.dropboxfn || EGeoXml.addDropdown;
  // elabel options 
  this.elabelopacity = this.opts.elabelopacity || 100;
  // other useful "global" stuff
  this.bounds = new GLatLngBounds();
  this.gmarkers = [];
  this.gpolylines = [];
  this.gpolygons = [];
  this.groundoverlays = [];
  this.side_bar_html = "";
  this.side_bar_list = [];
  this.styles = []; // associative array
  this.iwwidth = this.opts.iwwidth || 250;
  this.progress = 0;
  this.lastmarker = {};   
  this.myimages = [];
  this.imageNum =0;
}
               
// uses GXml.value, then removes leading and trailing whitespace
EGeoXml.value = function(e) {
  a = GXml.value(e);
  a = a.replace(/^\s*/,"");
  a = a.replace(/\s*$/,"");
  return a;
}

// Create Marker

EGeoXml.prototype.createMarker = function(point,name,desc,style) {
  var icon = G_DEFAULT_ICON;
  var myvar=this.myvar;
  var iwoptions = this.opts.iwoptions || {};
  var markeroptions = this.opts.markeroptions || {};
  var icontype = this.opts.icontype || "style";
  if (icontype == "style") {
    if (!!this.styles[style]) {
      icon = this.styles[style];
    }
  }
  if (!markeroptions.icon) {
    markeroptions.icon = icon;
  }
  var m = new GMarker(point, markeroptions);

  // Attempt to preload images
  if (this.opts.preloadimages) {
    var text = desc;
    var pattern = /<\s*img/ig;
    var result;
    var pattern2 = /src\s*=\s*[\'\"]/;
    var pattern3 = /[\'\"]/;

    while ((result = pattern.exec(text)) != null) {
      var stuff = text.substr(result.index);
      var result2 = pattern2.exec(stuff);
      if (result2 != null) {
        stuff = stuff.substr(result2.index+result2[0].length);
        var result3 = pattern3.exec(stuff);
        if (result3 != null) {
          var imageUrl = stuff.substr(0,result3.index);
          this.myimages[this.imageNum] = new Image();
          this.myimages[this.imageNum].src = imageUrl;
          this.imageNum++;
        }
      }
    }
  }



  if (this.opts.elabelclass) {
    var l = new ELabel(point, name, this.opts.elabelclass, this.opts.elabeloffset, this.elabelopacity, true);
    this.map.addOverlay(l);
  }

  var html = "<div style = 'width:"+this.iwwidth+"px'>"
               + "<h1 "+this.titlestyle+">"+name+"</h1>"
               +"<div "+this.descstyle+">"+desc+"</div>";

  if (this.opts.directions) {
    var html1 = html + '<div '+this.directionstyle+'>'
                     + 'Get Directions: <a href="javascript:GEvent.trigger(' + this.myvar +'.lastmarker,\'click2\')">To Here</a> - ' 
                     + '<a href="javascript:GEvent.trigger(' + this.myvar +'.lastmarker,\'click3\')">From Here</a><br>'
                     + '<a href="javascript:GEvent.trigger(' + this.myvar +'.lastmarker,\'click4\')">Search nearby</a></div>';
    var html2 = html + '<div '+this.directionstyle+'>'
                     + 'Get Directions: To here - '
                     + '<a href="javascript:GEvent.trigger(' + this.myvar +'.lastmarker,\'click3\')">From Here</a><br>'
                     + 'Start address:<form action="http://maps.google.com/maps" method="get" target="_blank">'
                     + '<input type="text" SIZE=35 MAXLENGTH=80 name="saddr" id="saddr" value="" />'
                     + '<INPUT value="Go" TYPE="SUBMIT">'
                     + '<input type="hidden" name="daddr" value="' + point.lat() + ',' + point.lng() + "(" + name + ")" + '"/>'
                     + '<br><a href="javascript:GEvent.trigger(' + this.myvar +'.lastmarker,\'click\')">&#171; Back</a></div>';
    var html3 = html + '<div '+this.directionstyle+'>'
                     + 'Get Directions: <a href="javascript:GEvent.trigger(' + this.myvar +'.lastmarker,\'click2\')">To Here</a> - ' 
                     + 'From Here<br>'
                     + 'End address:<form action="http://maps.google.com/maps" method="get"" target="_blank">'
                     + '<input type="text" SIZE=35 MAXLENGTH=80 name="daddr" id="daddr" value="" />'
                     + '<INPUT value="Go" TYPE="SUBMIT">'
                     + '<input type="hidden" name="saddr" value="' + point.lat() + ',' + point.lng() +  "(" + name + ")" + '"/>'
                     + '<br><a href="javascript:GEvent.trigger(' + this.myvar +'.lastmarker,\'click\')">&#171; Back</a></div>';
    var html4 = html + '<div '+this.directionstyle+'>'
                     + 'Search nearby: e.g. "pizza"<br>'
                     + '<form action="http://maps.google.com/maps" method="get"" target="_blank">'
                     + '<input type="text" SIZE=35 MAXLENGTH=80 name="q" id="q" value="" />'
                     + '<INPUT value="Go" TYPE="SUBMIT">'
                     + '<input type="hidden" name="near" value="' + name + ' @' + point.lat() + ',' + point.lng() + '"/>'
                   //  + '<input type="hidden" name="near" value="' +  point.lat() + ',' + point.lng() +  "(" + name + ")" + '"/>';
                     + '<br><a href="javascript:GEvent.trigger(' + this.myvar +'.lastmarker,\'click\')">&#171; Back</a></div>';
    GEvent.addListener(m, "click2", function() {
      m.openInfoWindowHtml(html2 + "</div>",iwoptions);
    });
    GEvent.addListener(m, "click3", function() {
      m.openInfoWindowHtml(html3 + "</div>",iwoptions);
    });
    GEvent.addListener(m, "click4", function() {
      m.openInfoWindowHtml(html4 + "</div>",iwoptions);
    });
  } else {
    var html1 = html;
  }

  GEvent.addListener(m, "click", function() {
    eval(myvar+".lastmarker = m");
    m.openInfoWindowHtml(html1 + "</div>",iwoptions);
  });
  if (!!this.opts.addmarker) {
    this.opts.addmarker(m,name,desc,icon.image,this.gmarkers.length)
  } else {
    this.map.addOverlay(m);
  }
  this.gmarkers.push(m);
  if (this.opts.sidebarid || this.opts.dropboxid) {
    var n = this.gmarkers.length-1;
    this.side_bar_list.push (name + "$$$marker$$$" + n +"$$$" );
  }
}

// Create Polyline

EGeoXml.prototype.createPolyline = function(points,color,width,opacity,pbounds,name,desc) {
  var thismap = this.map;
  var iwoptions = this.opts.iwoptions || {};
  var polylineoptions = this.opts.polylineoptions || {};
  var p = new GPolyline(points,color,width,opacity,polylineoptions);
  this.map.addOverlay(p);
  this.gpolylines.push(p);
  var html = "<div style='font-weight: bold; font-size: medium; margin-bottom: 0em;'>"+name+"</div>"
             +"<div style='font-family: Arial, sans-serif;font-size: small;width:"+this.iwwidth+"px'>"+desc+"</div>";
  GEvent.addListener(p,"click", function() {
    thismap.openInfoWindowHtml(p.getVertex(Math.floor(p.getVertexCount()/2)),html,iwoptions);
  } );
  if (this.opts.sidebarid) {
    var n = this.gpolylines.length-1;
    var blob = '&nbsp;&nbsp;<span style=";border-left:'+width+'px solid '+color+';">&nbsp;</span> ';
    this.side_bar_list.push (name + "$$$polyline$$$" + n +"$$$" + blob );
  }
}

// Create Polygon

EGeoXml.prototype.createPolygon = function(points,color,width,opacity,fillcolor,fillopacity,pbounds, name, desc) {
  var thismap = this.map;
  var iwoptions = this.opts.iwoptions || {};
  var polygonoptions = this.opts.polygonoptions || {};
  var p = new GPolygon(points,color,width,opacity,fillcolor,fillopacity,polygonoptions)
  this.map.addOverlay(p);
  this.gpolygons.push(p);
  var html = "<div style='font-weight: bold; font-size: medium; margin-bottom: 0em;'>"+name+"</div>"
             +"<div style='font-family: Arial, sans-serif;font-size: small;width:"+this.iwwidth+"px'>"+desc+"</div>";
  GEvent.addListener(p,"click", function() {
    thismap.openInfoWindowHtml(pbounds.getCenter(),html,iwoptions);
  } );
  if (this.opts.sidebarid) {
    var n = this.gpolygons.length-1;
    var blob = '<span style="background-color:' +fillcolor + ';border:2px solid '+color+';">&nbsp;&nbsp;&nbsp;&nbsp;</span> ';
    this.side_bar_list.push (name + "$$$polygon$$$" + n +"$$$" + blob );
  }
}


// Sidebar factory method One - adds an entry to the sidebar
EGeoXml.addSidebar = function(myvar,name,type,i,graphic) {
  if (type == "marker") {
    return '<a href="javascript:GEvent.trigger(' + myvar+ '.gmarkers['+i+'],\'click\')">' + name + '</a><br>';
  }
  if (type == "polyline") {
    return '<div style="margin-top:6px;"><a href="javascript:GEvent.trigger(' + myvar+ '.gpolylines['+i+'],\'click\')">' + graphic + name + '</a></div>';
  }
  if (type == "polygon") {
    return '<div style="margin-top:6px;"><a href="javascript:GEvent.trigger(' + myvar+ '.gpolygons['+i+'],\'click\')">' + graphic + name + '</a></div>';
  }
}

// Dropdown factory method
EGeoXml.addDropdown = function(myvar,name,type,i,graphic) {
    return '<option value="' + i + '">' + name +'</option>';
}

  
// Request to Parse an XML file

EGeoXml.prototype.parse = function() {
  // clear some variables
  this.gmarkers = [];
  this.gpolylines = [];
  this.gpolygons = [];
  this.groundoverlays = [];
  this.side_bar_html = "";
  this.side_bar_list = [];
  this.styles = []; // associative array
  this.lastmarker = {};   
  this.myimages = [];
  this.imageNum =0;
  var that = this;
  this.progress = this.urls.length;
  for (u=0; u<this.urls.length; u++) {
    GDownloadUrl(this.urls[u], function(doc) {that.processing(doc)});
  }
}

EGeoXml.prototype.parseString = function(doc) {
  // clear some variables
  this.gmarkers = [];
  this.gpolylines = [];
  this.gpolygons = [];
  this.groundoverlays = [];
  this.side_bar_html = "";
  this.side_bar_list = [];
  this.styles = []; // associative array
  this.lastmarker = {};   
  this.myimages = [];
  this.imageNum =0;
  if (typeof doc == "string") {
    this.docs = [doc];
  } else {
    this.docs = doc;
  }
  this.progress = this.docs.length;
  for (u=0; u<this.docs.length; u++) {
    this.processing(this.docs[u]);
  }
}


EGeoXml.prototype.processing = function(doc) {
    var that = this;
    var xmlDoc = GXml.parse(doc)
    // Read through the Styles
    var styles = xmlDoc.documentElement.getElementsByTagName("Style");
    for (var i = 0; i <styles.length; i++) {
      var styleID = styles[i].getAttribute("id");
      var icons=styles[i].getElementsByTagName("Icon");
      // This might not be am icon style
      if (icons.length > 0) {
        var href=EGeoXml.value(icons[0].getElementsByTagName("href")[0]);
        if (!!href) {
          if (!!that.opts.baseicon) {
            that.styles["#"+styleID] = new GIcon(that.opts.baseicon,href);
          } else {
            that.styles["#"+styleID] = new GIcon(G_DEFAULT_ICON,href);
            that.styles["#"+styleID].iconSize = new GSize(32,32);
            that.styles["#"+styleID].shadowSize = new GSize(59,32);
            that.styles["#"+styleID].dragCrossAnchor = new GPoint(2,8);
            that.styles["#"+styleID].iconAnchor = new GPoint(16,32);
            if (that.opts.printgif) {
              var bits = href.split("/");
              var gif = bits[bits.length-1];
              gif = that.opts.printgifpath + gif.replace(/.png/i,".gif");
              that.styles["#"+styleID].printImage = gif;
              that.styles["#"+styleID].mozPrintImage = gif;
            }
            if (!!that.opts.noshadow) {
              that.styles["#"+styleID].shadow="";
            } else {
              // Try to guess the shadow image
              if (href.indexOf("/red.png")>-1 
               || href.indexOf("/blue.png")>-1 
               || href.indexOf("/green.png")>-1 
               || href.indexOf("/yellow.png")>-1 
               || href.indexOf("/lightblue.png")>-1 
               || href.indexOf("/purple.png")>-1 
               || href.indexOf("/pink.png")>-1 
               || href.indexOf("/orange.png")>-1 
               || href.indexOf("-dot.png")>-1 ) {
                  that.styles["#"+styleID].shadow="http://maps.google.com/mapfiles/ms/micons/msmarker.shadow.png";
              }
              else if (href.indexOf("-pushpin.png")>-1) {
                  that.styles["#"+styleID].shadow="http://maps.google.com/mapfiles/ms/micons/pushpin_shadow.png";
              }
              else {
                var shadow = href.replace(".png",".shadow.png");
                that.styles["#"+styleID].shadow=shadow;
              }
            }
          }
        }
      }
      // is it a LineStyle ?
      var linestyles=styles[i].getElementsByTagName("LineStyle");
      if (linestyles.length > 0) {
        var width = parseInt(GXml.value(linestyles[0].getElementsByTagName("width")[0]));
        if (width < 1) {width = 5;}
        var color = EGeoXml.value(linestyles[0].getElementsByTagName("color")[0]);
        var aa = color.substr(0,2);
        var bb = color.substr(2,2);
        var gg = color.substr(4,2);
        var rr = color.substr(6,2);
        color = "#" + rr + gg + bb;
        var opacity = parseInt(aa,16)/256;
        if (!that.styles["#"+styleID]) {
          that.styles["#"+styleID] = {};
        }
        that.styles["#"+styleID].color=color;
        that.styles["#"+styleID].width=width;
        that.styles["#"+styleID].opacity=opacity;
      }
      // is it a PolyStyle ?
      var polystyles=styles[i].getElementsByTagName("PolyStyle");
      if (polystyles.length > 0) {
        var fill = parseInt(GXml.value(polystyles[0].getElementsByTagName("fill")[0]));
        var outline = parseInt(GXml.value(polystyles[0].getElementsByTagName("outline")[0]));
        var color = EGeoXml.value(polystyles[0].getElementsByTagName("color")[0]);

        if (polystyles[0].getElementsByTagName("fill").length == 0) {fill = 1;}
        if (polystyles[0].getElementsByTagName("outline").length == 0) {outline = 1;}
        var aa = color.substr(0,2);
        var bb = color.substr(2,2);
        var gg = color.substr(4,2);
        var rr = color.substr(6,2);
        color = "#" + rr + gg + bb;

        var opacity = parseInt(aa,16)/256;
        if (!that.styles["#"+styleID]) {
          that.styles["#"+styleID] = {};
        }
        that.styles["#"+styleID].fillcolor=color;
        that.styles["#"+styleID].fillopacity=opacity;
        if (!fill) that.styles["#"+styleID].fillopacity = 0; 
        if (!outline) that.styles["#"+styleID].opacity = 0; 
      }
    }

    // Read through the Placemarks
    var placemarks = xmlDoc.documentElement.getElementsByTagName("Placemark");
    for (var i = 0; i < placemarks.length; i++) {
      var name=EGeoXml.value(placemarks[i].getElementsByTagName("name")[0]);
      var desc=EGeoXml.value(placemarks[i].getElementsByTagName("description")[0]);
      if (desc=="") {
        var desc=EGeoXml.value(placemarks[i].getElementsByTagName("text")[0]);
        desc = desc.replace(/\$\[name\]/,name);
        desc = desc.replace(/\$\[geDirections\]/,"");
      }
      if (desc.match(/^http:\/\//i)) {
        desc = '<a href="' + desc + '">' + desc + '</a>';
      }
      if (desc.match(/^https:\/\//i)) {
        desc = '<a href="' + desc + '">' + desc + '</a>';
      }
      var style=EGeoXml.value(placemarks[i].getElementsByTagName("styleUrl")[0]);
      var coords=GXml.value(placemarks[i].getElementsByTagName("coordinates")[0]);
      coords=coords.replace(/\s+/g," "); // tidy the whitespace
      coords=coords.replace(/^ /,"");    // remove possible leading whitespace
      coords=coords.replace(/ $/,"");    // remove possible trailing whitespace
      coords=coords.replace(/, /,",");   // tidy the commas
      var path = coords.split(" ");

      // Is this a polyline/polygon?
      if (path.length > 1) {
        // Build the list of points
        var points = [];
        var pbounds = new GLatLngBounds();
        for (var p=0; p<path.length; p++) {
          var bits = path[p].split(",");
          var point = new GLatLng(parseFloat(bits[1]),parseFloat(bits[0]));
          points.push(point);
          that.bounds.extend(point);
          pbounds.extend(point);
        }
        var linestring=placemarks[i].getElementsByTagName("LineString");
        if (linestring.length) {
          // it's a polyline grab the info from the style
          if (!!that.styles[style]) {
            var width = that.styles[style].width; 
            var color = that.styles[style].color; 
            var opacity = that.styles[style].opacity; 
          } else {
            var width = 5;
            var color = "#0000ff";
            var opacity = 0.45;
          }
          // Does the user have their own createmarker function?
          if (!!that.opts.createpolyline) {
            that.opts.createpolyline(points,color,width,opacity,pbounds,name,desc);
          } else {
            that.createPolyline(points,color,width,opacity,pbounds,name,desc);
          }
        }

        var polygons=placemarks[i].getElementsByTagName("Polygon");
        if (polygons.length) {
          // it's a polygon grab the info from the style
          if (!!that.styles[style]) {
            var width = that.styles[style].width; 
            var color = that.styles[style].color; 
            var opacity = that.styles[style].opacity; 
            var fillopacity = that.styles[style].fillopacity; 
            var fillcolor = that.styles[style].fillcolor; 
          } else {
            var width = 5;
            var color = "#0000ff";
            var opacity = 0.45;
            var fillopacity = 0.25;
            var fillcolor = "#0055ff";
          }
          // Does the user have their own createmarker function?
          if (!!that.opts.createpolygon) {
            that.opts.createpolygon(points,color,width,opacity,fillcolor,fillopacity,pbounds,name,desc);
          } else {
            that.createPolygon(points,color,width,opacity,fillcolor,fillopacity,pbounds,name,desc);
          }
        }


      } else {
        // It's not a poly, so I guess it must be a marker
        var bits = path[0].split(",");
        var point = new GLatLng(parseFloat(bits[1]),parseFloat(bits[0]));
        that.bounds.extend(point);
        // Does the user have their own createmarker function?
        if (!!that.opts.createmarker) {
          that.opts.createmarker(point, name, desc, style);
        } else {
          that.createMarker(point, name, desc, style);
        }
      }
    }
    
    // Scan through the Ground Overlays
    var grounds = xmlDoc.documentElement.getElementsByTagName("GroundOverlay");
    for (var i = 0; i < grounds.length; i++) {
      var url=EGeoXml.value(grounds[i].getElementsByTagName("href")[0]);
      var north=parseFloat(GXml.value(grounds[i].getElementsByTagName("north")[0]));
      var south=parseFloat(GXml.value(grounds[i].getElementsByTagName("south")[0]));
      var east=parseFloat(GXml.value(grounds[i].getElementsByTagName("east")[0]));
      var west=parseFloat(GXml.value(grounds[i].getElementsByTagName("west")[0]));
      var sw = new GLatLng(south,west);
      var ne = new GLatLng(north,east);                           
      var ground = new GGroundOverlay(url, new GLatLngBounds(sw,ne));
      that.bounds.extend(sw); 
      that.bounds.extend(ne); 
      that.groundoverlays.push(ground);
      that.map.addOverlay(ground);
    }

    // Is this the last file to be processed?
    that.progress--;
    if (that.progress == 0) {
      // Shall we zoom to the bounds?
      if (!that.opts.nozoom) {
        that.map.setZoom(that.map.getBoundsZoomLevel(that.bounds));
        that.map.setCenter(that.bounds.getCenter());
      }
      // Shall we display the sidebar?
      if (that.opts.sortbyname) {
        that.side_bar_list.sort();
      }
      if (that.opts.sidebarid) {
        for (var i=0; i<that.side_bar_list.length; i++) {
          var bits = that.side_bar_list[i].split("$$$",4);
          that.side_bar_html += that.sidebarfn(that.myvar,bits[0],bits[1],bits[2],bits[3]); 
        }
        document.getElementById(that.opts.sidebarid).innerHTML += that.side_bar_html;
      }
      if (that.opts.dropboxid) {
        for (var i=0; i<that.side_bar_list.length; i++) {
          var bits = that.side_bar_list[i].split("$$$",4);
          if (bits[1] == "marker") {
            that.side_bar_html += that.dropboxfn(that.myvar,bits[0],bits[1],bits[2],bits[3]); 
          }
        }
        document.getElementById(that.opts.dropboxid).innerHTML = '<select onChange="var I=this.value;if(I>-1){GEvent.trigger('+that.myvar+'.gmarkers[I],\'click\'); }">'
          + '<option selected> - Select a location - </option>'
          + that.side_bar_html
          + '</select>';
      }

      GEvent.trigger(that,"parsed");
    }
}

EGeoXml.prototype.hide = function() {
  for (var i=0; i<this.gmarkers.length; i++) {
    this.gmarkers[i].hide();
  }
  for (var i=0; i<this.gpolylines.length; i++) {
    this.gpolylines[i].hide();
  }
  for (var i=0; i<this.gpolygons.length; i++) {
    this.gpolygons[i].hide();
  }
  for (var i=0; i<this.groundoverlays.length; i++) {
    this.groundoverlays[i].hide();
  }
  if (this.opts.sidebarid) {
    document.getElementById(this.opts.sidebarid).style.display="none";
  }
  if (this.opts.dropboxid) {
    document.getElementById(this.opts.dropboxid).style.display="none";
  }
}

EGeoXml.prototype.show = function() {
  for (var i=0; i<this.gmarkers.length; i++) {
    this.gmarkers[i].show();
  }
  for (var i=0; i<this.gpolylines.length; i++) {
    this.gpolylines[i].show();
  }
  for (var i=0; i<this.gpolygons.length; i++) {
    this.gpolygons[i].show();
  }
  for (var i=0; i<this.groundoverlays.length; i++) {
    this.groundoverlays[i].show();
  }
  if (this.opts.sidebarid) {
    document.getElementById(this.opts.sidebarid).style.display="";
  }
  if (this.opts.dropboxid) {
    document.getElementById(this.opts.dropboxid).style.display="";
  }
}

