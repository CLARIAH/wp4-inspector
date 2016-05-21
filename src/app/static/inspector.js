  var socket = io.connect('http://' + document.domain + ':' + location.port + '/');
  var force;

  var types = new Set([]);
  var typemap = {};
  var origins = new Set([]);
  var originmap = {};

  socket.on('connect', function() {
    socket.emit('message', {data: 'Inspector is connected!'});
  });

  socket.on('response', function(msg) {
    console.log(msg);
  });

  socket.on('update', function(msg){
    console.log('Inspector is being updated...')
    console.log(msg.data);
    var nodes = msg.data.nodes;
    var links = msg.data.links;

    fnodes = force.nodes();
    flinks = force.links();

    fnodes.push.apply(fnodes,nodes);
    flinks.push.apply(flinks,links);

    // force.nodes().apply(force.nodes(),nodes);
    // force.edges().apply(force.edges(),edges);

    force.start();
  });


  // First time we load...
  $(function() {
      $.get('/graph', function(data){
        force = init_graph(data);
      });
  });


  function init_graph(graph){
    var width = 1500,
        height = 1500;

    // var color = d3.scale.category20b();
    var color2 = d3.scale.ordinal().range(colorbrewer.RdBu[11]);

    var color = d3.scale.ordinal().range(colorbrewer.Paired[3]);

    var force = d3.layout.force()
        .charge(-320)
        .linkDistance(50)
        .size([width, height]);

    var zoom = d3.behavior.zoom()
        .scaleExtent([.1, 10])
        .on("zoom", zoomed);



    var svg = d3.select("#graph").append("svg")
        .attr("width", width)
        .attr("height", height)
        .call(zoom);


    var tip = d3.tip()
      .attr('class', 'd3-tip')
      .offset([-10, 0])
      .html(function(d) {
        if (d.type == 'person' && d.label != undefined ){
          var content = "<h5>" + d.label + "</h5>"+
                 "<img src='"+ d.image +"'></img>";
        } else if (d.type == 'person' && d.label == 'datalegend' ) {
          var content = "<img src='static/datalegend-text-white-small-96dpi.png'></img>";
        } else {
          var content = "<h5>" + d.name.replace('http://data.socialhistory.org/resource/','csdh:') + "</h5>"+
                //  "<strong>Type:</strong> <span style='color: "+ color(d.type) +";'>" + d.type + "</span><br/>" +
                 "<strong>Origin:</strong> <span style='color: "+ color2(d.origin) +";'>" + d.origin.replace('http://data.socialhistory.org/resource/','csdh:') + "</span>";
        }
        return content
      });

    svg.call(tip);

    var container = svg.append("g");

    force
        .nodes(graph.nodes)
        .links(graph.links)
        .start();



    var link = container.append("g")
                        .attr("class", "links")
                        .selectAll(".link")
			.data(graph.links)
        .enter().append("line")
        .attr("class", "link")
        .style("stroke-width", function(d) { return 2; }); // Math.sqrt(d.value); });

    var node = container.append("g")
                        .attr("class","nodes")
                        .selectAll(".node")
        .data(graph.nodes)
      .enter().append("g")
        .attr("class", "node")
        .call(force.drag)
        // .on('mouseover', tip.show)
        // .on('mouseout', tip.hide)
        .on('click', function(d){
          if (d3.event.defaultPrevented) return;
          window.open('http://data.clariah-sdh.eculture.labs.vu.nl/browse?uri=' + encodeURIComponent(d.name));
        });

    node.append("title")
        .text(function(d) { console.log(d); return d.name.replace('http://data.socialhistory.org/resource/','csdh:'); });

    var linkedByIndex = {};
    graph.links.forEach(function(d) {
        linkedByIndex[d.source.index + "," + d.target.index] = 1;
    });

    function isConnected(a, b) {
        return linkedByIndex[a.index + "," + b.index] || linkedByIndex[b.index + "," + a.index];
    }

    node.on("mouseover", function(d){
                            tip.show(d);
                            node.classed("node-active", function(o) {
                                thisOpacity = isConnected(d, o) ? true : false;
                                this.setAttribute('fill-opacity', thisOpacity);
                                return thisOpacity;
                            });

                            link.classed("link-active", function(o) {
                                return o.source === d || o.target === d ? true : false;
                            });

                            d3.select(this).classed("node-active", true);
                            d3.select(this).select("circle").transition()
                                    .duration(750)
                                    .attr("r", (d.weight * 2+ 12)*1.5);
                    })

    		.on("mouseout", function(d){
                            tip.hide(d);
                            node.classed("node-active", false);
                            link.classed("link-active", false);
                          });

    function zoomed() {
      container.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
    }

    node.append("text")
        .attr('font-family', 'FontAwesome')
        .attr('font-size', function(d){ return '2em';})
        .attr('alignment-baseline', 'middle')
        .attr('text-anchor', 'middle')
        .attr('fill', function(d){
                              if (d.type == 'person') {
                                return "#000";
                              } else {
                                originmap[d.origin] = color2(d.origin); return color2(d.origin);
                              }
        })
        .text(function(d) {
                            if (d.type == 'person' && d.label == 'datalegend'){
                              return '\uf085';
                            } else if (d.type == 'person' && d.label != undefined ){
                              return '\uf007';
                            } else if (d.type == 'dataset'){
                              return '\uf1b3';
                            } else if (d.type == 'dimension' && d.origin == 'external'){
                              return '\uf0c2';
                            } else if (d.type == 'dimension'){
                              return '\uf0c8';
                            }

                          });


    force.on("tick", function() {
      link.attr("x1", function(d) { return d.source.x; })
          .attr("y1", function(d) { return d.source.y; })
          .attr("x2", function(d) { return d.target.x; })
          .attr("y2", function(d) { return d.target.y; });

      node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
      node.attr("cx", function(d) { return d.x; })
          .attr("cy", function(d) { return d.y; });
    });

    return force
}
