$(function ($) {
  // Constants
  var hydraulicsHost = 'localhost' // XXX change this to a real thing
  var flameHost = 'localhost' // XXX change this to a real thing
  var pollingInterval = 1000 // in milliseconds

  // Initial values
  var selectedPoofer = null
  var inverted = false

  // Helper functions
  var flameUrl = function(endpoint) {
    return `http://${flameHost}/${endpoint}`
  }
  var hydraulicsUrl = function(endpoint) {
    return `http://${hydraulicsHost}/${endpoint}`
  }

  // jQuery helper functions
  var findPoofer = function(name) {
    return $('.poofer-' + name)
  }

  // Display state update functions
  var updatePooferToggleButtonState = function() {
    $('.poofer-individual-toggle-button').text(selectedPoofer.firing ? 'Stop' : 'Start')
  }
  var updateSelectedPooferName = function() {
    $('.poofer-selected-display-field').html(selectedPoofer.name)
  }
  var updateSelectedPooferDependentState = function() {
    updateSelectedPooferName()
    updatePooferToggleButtonState()
  }
  var updatePooferDisplayState = function(poofer) {
    var $poofer = findPoofer(poofer.name)
    if (poofer.firing) {
      $poofer.addClass('poofer-firing')
    } else {
      $poofer.removeClass('poofer-firing')
    }
  }
  var updateAllPoofersDisplayState = function() {
    allPoofers.forEach(function (pooferName) {
      var poofer = allPoofersState[pooferName]
      updatePooferDisplayState(poofer)
    })
  }
  var updateEverything = function() {
    updateSelectedPooferDependentState()
    updateAllPoofersDisplayState()
  }

  // Data state setting functions
  var setSelectedPoofer = function(name) {
    selectedPoofer = allPoofersState[name]
    updateSelectedPooferDependentState()
  }
  var updatePooferDate = function (data) {
    data.forEach(function(poofer) {
      var pooferState = allPoofersState[poofer.name]
      pooferState.firing = poofer.firing
    })
  }

  // Setup poofer data structures
  var allPoofers = ['nn','nw','nt','ne','wn','tn','en','ww','wt','tw','tt','te','et','ee','ws','ts','es','sw','st','se','ss','bn','bs','be','bw']
  var PooferState = function(name) {
    this.name = name
    this.firing = false
    return this
  }
  var allPoofersState = {}
  for (var i = 0; i < allPoofers.length; i++) {
    var name = allPoofers[i]
    allPoofersState[name] = new PooferState(name)
    // Setup poofer event handlers
    var $currentPoofer = findPoofer(name)
    ;(function () {
      var tempName = name
      $currentPoofer.on('click', function () {
        setSelectedPoofer(tempName)
      })
    })()
  }

  // Setup button event handlers
  $('.invert-button').on('click', function () {
    if (inverted) {
      inverted = false
      $('html').removeClass('inverted')
    } else {
      inverted = true
      $('html').addClass('inverted')
    }
  })
  $('.poofer-individual-toggle-button').on('click', function () {
    if (selectedPoofer) {
      selectedPoofer.firing = !selectedPoofer.firing
      updatePooferDisplayState(selectedPoofer)
      updatePooferToggleButtonState()
      $.post(flameUrl(`poofers/${selectedPoofer.name}`), { enabled: selectedPoofer.firing })
    }
  })

  var pollingFunction = function() {
    var polling = $('.polling-checkbox').is(':checked')
    if (!polling) return
    $.get(flameUrl('flame')).done(function(data) {
      updatePooferData(data)
      updateEverything()
    })
  }
  setInterval(pollingFunction, pollingInterval)
})
