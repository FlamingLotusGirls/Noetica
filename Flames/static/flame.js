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
  var selectedFilename = null
  var hydraulicsAttractMode = false

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
    var addedFiles = []
    var removedFiles = []
    hydraulicsAttractFiles.forEach(function(file) {
      var fileInList = $files.reduce(function(acc, cur) {
        var $cur = $(cur)
        return acc || $cur.data('name') === file
      }, false)
      if (!fileInList) {
        addedFiles.push(file)
      }
    })
    $files.each(function(idx, file) {
      var $file = $(file)
      var fileInList = hydraulicsAttractFiles.reduce(function(acc, cur) {
        return acc || $file.data('name') === cur
      }, false)
      if (!fileInList) {
        removedFiles.push($file)
        if ($file.hasClass('selected')) {
          selectedFilename = null
        }
      }
    })
    removedFiles.forEach(function($file) {
      $fileList.removeChild($file)
    })
    addedFiles.forEach(function(file) {
      var $file = $(`<li class="hydraulics-attract-file" data-name="${file}">${file}</li>`)
      $fileList.append($file)
    })
  }
  var updateHydraulicsAttractPlayMode = function() {
    var oldMode = hydraulicsAttractMode
    if (!selectedFilename) {
      hydraulicsAttractMode = false
      $('.hydraulics-attract-play-stop-button').attr('disabled', true)
      $('.hydraulics-attract-play-stop-button').text('Start')
    } else {
      $('.hydraulics-attract-play-stop-button').attr('disabled', false)
    }
    $('.hydraulics-attract-play-stop-button').text(hydraulicsAttractMode ? 'Stop' : 'Start')
    if (hydraulicsAttractMode !== oldMode) {
      postHydraulicsAttractMode()
    }
  }
  var updateSelectedFileDependentState = function() {
    updateHydraulicsAttractPlayMode()
  }
  var updateEverything = function() {
    updateSelectedPooferDependentState()
    updateAllPoofersDisplayState()
    updateHydraulicsAttractFilePicker()
    updateSelectedFileDependentState()
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
  $('.hydraulics-attract-file-picker').on('click', function(event) {
    var $selectedItem = $(event.target)
    if ($selectedItem.length === 0 || !$selectedItem.hasClass('hydraulics-attract-file')) {
      return
    }
    selectedFilename = $selectedItem.data('name')
    if (!$selectedItem.hasClass('selected')) {
      $('.hydraulics-attract-file-picker li').removeClass('selected')
      $selectedItem.addClass('selected')
    }
    updateEverything()
  })
  $('.hydraulics-attract-play-stop-button').on('click', function() {
    hydraulicsAttractMode = !hydraulicsAttractMode
    postHydraulicsAttractMode()
    updateEverything()
  })

  // Ajax functions
  var postHydraulicsAttractMode = function() {
    if (hydraulicsAttractMode && selectedFilename) {
      $.post(hydraulicsUrl('hydraulics'), {
        state: 1,
        currentPlayback: selectedFilename
      })
    } else {
      // just in case, make state consistent
      hydraulicsAttractMode = false
      $.post(hydraulicsUrl('hydraulics'), {
        state: 0
      })
    }
  }

  // Setup polling
  var pollingFunction = function() {
    var polling = $('.polling-checkbox').is(':checked')
    if (!polling) return
    $.get(flameUrl('flame')).done(function(data) {
      updatePooferData(data)
      updateEverything()
    })
  }
  setInterval(pollingFunction, pollingInterval)

  // Make sure initial UI state is correct
  updateEverything()
})
