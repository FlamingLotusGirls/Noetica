$(function ($) {
  // Constants
  var hydraulicsHost = 'localhost' // XXX change this to a real thing
  var flameHost = 'localhost' // XXX change this to a real thing
  var pollingInterval = 1000 // in milliseconds

  // Test values
  var hydraulicsAttractFiles = ['wicked poof', 'poofy smurf', 'superfly', 'black sunshine']

  // Initial values
  var selectedPoofer = null
  var inverted = false

  // jQuery helpers
  $.fn.reduce = function() {
    return [].reduce.apply(this.toArray(), arguments)
  }

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
    var enabled = !selectedPoofer || selectedPoofer.enabled
    $('.poofer-individual-toggle-button').text(enabled ? 'Stop' : 'Start')
  }
  var updateSelectedPooferName = function() {
    var name = (selectedPoofer && selectedPoofer.name) || ''
    $('.poofer-selected-display-field').html(name)
  }
  var updateSelectedPooferDependentState = function() {
    updateSelectedPooferName()
    updatePooferToggleButtonState()
  }
  var updatePooferDisplayState = function(poofer) {
    var $poofer = findPoofer(poofer.name)
    if (poofer.enabled) {
      $poofer.addClass('poofer-enabled')
    } else {
      $poofer.removeClass('poofer-enabled')
    }
  }
  var updateAllPoofersDisplayState = function() {
    allPoofers.forEach(function (pooferName) {
      var poofer = allPoofersState[pooferName]
      updatePooferDisplayState(poofer)
    })
  }
  var updateHydraulicsAttractFilePicker = function() {
    var $files = $('.hydraulics-attract-file')
    var $fileList = $('.hydraulics-attract-file-picker')
    console.log($files, $fileList)
    var addedFiles = []
    var removedFiles = []
    hydraulicsAttractFiles.forEach(function(file) {
      console.log('hydraulicsAttractFiles.forEach called')
      var fileInList = $files.reduce(function(acc, $cur) {
        return acc || $cur.data('name') === file
      }, false)
      console.log(fileInList)
      if (!fileInList) {
        addedFiles.push(file)
      }
    })
    console.log(addedFiles)
    $files.each(function($file) {
      console.log('$files.each called')
      var fileInList = hydraulicsAttractFiles.reduce(function(acc, cur) {
        return acc || $file.data('name') === cur
      }, false)
      if (!fileInList) {
        removedFiles.push($file)
      }
    })
    console.log(removedFiles)

    removedFiles.forEach(function($file) {
      $fileList.removeChild($file)
    })
    addedFiles.forEach(function(file) {
      var $file = $(`<li class="hydraulics-attract-file" data-name="${file}"><a href="#">${file}</a></li>`)
      $fileList.append($file)
    })
    $fileList.listview('refresh')
  }
  var updateEverything = function() {
    console.log('about to update everything')
    updateSelectedPooferDependentState()
    updateAllPoofersDisplayState()
    updateHydraulicsAttractFilePicker()
  }

  // Data state setting functions
  var setSelectedPoofer = function(name) {
    selectedPoofer = allPoofersState[name]
    updateSelectedPooferDependentState()
  }
  var updatePooferDate = function (data) {
    data.forEach(function(poofer) {
      var pooferState = allPoofersState[poofer.name]
      pooferState.enabled = poofer.enabled
    })
  }

  // Setup poofer data structures
  var allPoofers = ['nn','nw','nt','ne','wn','tn','en','ww','wt','tw','tt','te','et','ee','ws','ts','es','sw','st','se','ss','bn','bs','be','bw']
  var PooferState = function(name) {
    this.name = name
    this.enabled = true
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
      selectedPoofer.enabled = !selectedPoofer.enabled
      updatePooferDisplayState(selectedPoofer)
      updatePooferToggleButtonState()
      $.post(flameUrl(`poofers/${selectedPoofer.name}`), { enabled: selectedPoofer.enabled })
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
  updateEverything()
})
