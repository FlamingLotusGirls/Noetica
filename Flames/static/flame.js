$(function ($) {
  // Constants
  var flameHost = 'noetica-flames.local'
  var pollingInterval = 1000 // in milliseconds
  var prefixes = {
    hydraulics: 'hydraulics-attract',
    poofer: 'poofer-sequence'
  }

  // Test values - replace these with empty arrays in prod
  var hydraulicsAttractFiles = ['wicked poof', 'poofy smurf', 'superfly', 'black sunshine']
  var pooferSequenceFiles = ['poofy pooferson', 'poof daddy', 'sugar poof', 'poofy mcpoofface']

  // Initial values
  var selectedPoofer = null
  var inverted = false
  var selectedFilenames = {}
  var hydraulicsAttractMode = false
  var hydraulicsState = {x:0,y:0,z:0,pid_x:0,pid_y:0,pid_z:0}

  // jQuery helpers
  $.fn.reduce = function() {
    return [].reduce.apply(this.toArray(), arguments)
  }

  // Helper functions
  var flameUrl = function(endpoint) {
    return `http://${flameHost}/${endpoint}`
  }
  var getOrSetFilename = function(prefix, filename) {
    if (filename !== undefined) {
      selectedFilenames[prefix] = filename
    }
    return selectedFilenames[prefix]
  }
  var selectedHydraulicsFilename = function(filename) {
    return getOrSetFilename(prefixes.hydraulics, filename)
  }
  var selectedPooferFilename = function(filename) {
    return getOrSetFilename(prefixes.poofer, filename)
  }

  // jQuery helper functions
  var findPoofer = function(name) {
    return $('.poofer-' + name)
  }

  // Display state update functions
  var updatePooferToggleButtonState = function() {
    var enabled = !selectedPoofer || selectedPoofer.enabled
    $('.poofer-individual-toggle-button').text(enabled ? 'Disable' : 'Enable')
  }
  var updateSelectedPooferName = function() {
    var name = (selectedPoofer && selectedPoofer.name) || 'None'
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
  var updateHydraulicsDisplayState = function() {
    ['x','y','z','pid_x','pid_y','pid_z'].forEach(function(coord) {
      $(`.hydraulics-label-${coord}`).text(hydraulicsState[coord])
    })
  }
  var updateFilePicker = function(prefix, fileList) {
    var $files = $(`.${prefix}-file`)
    var $fileList = $(`.${prefix}-file-picker`)
    var addedFiles = []
    var removedFiles = []
    fileList.forEach(function(file) {
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
      var fileInList = fileList.reduce(function(acc, cur) {
        return acc || $file.data('name') === cur
      }, false)
      if (!fileInList) {
        removedFiles.push($file)
        if ($file.hasClass('selected')) {
          selectedFilenames[prefix] = null
        }
      }
    })
    removedFiles.forEach(function($file) {
      $fileList.removeChild($file)
    })
    addedFiles.forEach(function(file) {
      var $file = $(`<li class="${prefix}-file sequence-file" data-name="${file}">${file}</li>`)
      $fileList.append($file)
    })
  }
  var updateHydraulicsAttractFilePicker = function() {
    updateFilePicker(prefixes.hydraulics, hydraulicsAttractFiles)
  }
  var updatePooferSequenceFilePicker = function() {
    updateFilePicker(prefixes.poofer, pooferSequenceFiles)
  }
  var updateHydraulicsAttractPlayMode = function() {
    var oldMode = hydraulicsAttractMode
    if (!selectedHydraulicsFilename()) {
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
  var updateAllUIState = function() {
    // Since we don't have automatic data binding and it's a pain to call update functions
    // in just the right places, this function just updates everything and is called
    // when anything changes. Where possible, functions called from here should be
    // written to not force refreshes of state that didn't actually change.
    updateSelectedPooferDependentState()
    updateAllPoofersDisplayState()
    updateHydraulicsDisplayState()
    updateHydraulicsAttractFilePicker()
    updatePooferSequenceFilePicker()
    updateSelectedFileDependentState()
  }

  // Data state setting functions
  var setSelectedPoofer = function(name) {
    selectedPoofer = allPoofersState[name]
    updateSelectedPooferDependentState()
  }
  var updatePooferData = function (data) {
    data.forEach(function(poofer) {
      var pooferState = allPoofersState[poofer.name]
      pooferState.enabled = poofer.enabled
    })
  }
  var updateHydraulicsData = function (data) {
    hydraulicsState = data
    hydraulicsAttractFiles = data.playbacks
    hydraulicsFileName(data.currentPlayback)
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
  Object.keys(prefixes).forEach(function(prefixKey) {
    var prefix = prefixes[prefixKey]
    $(`.${prefix}-file-picker`).on('click', function(event) {
      var $selectedItem = $(event.target)
      if ($selectedItem.length === 0 || !$selectedItem.hasClass(`${prefix}-file`)) {
        return
      }
      selectedFilenames[prefix] = $selectedItem.data('name')
      if (!$selectedItem.hasClass('selected')) {
        $(`.${prefix}-file-picker li`).removeClass('selected')
        $selectedItem.addClass('selected')
      }
      postAttractFile(prefix)
      updateAllUIState()
    })
  })
  $('.hydraulics-attract-play-stop-button').on('click', function() {
    hydraulicsAttractMode = !hydraulicsAttractMode
    postHydraulicsAttractMode()
    updateAllUIState()
  })

  // Ajax functions
  var postHydraulicsAttractMode = function() {
    if (hydraulicsAttractMode && selectedHydraulicsFilename()) {
      $.post(flameUrl('hydraulics'), {
        state: 1,
        currentPlayback: selectedHydraulicsFilename()
      })
    } else {
      // just in case, make state consistent
      hydraulicsAttractMode = false
      $.post(flameUrl('hydraulics'), {
        state: 0
      })
    }
  }
  var postAttractFile = function(prefix) {
    var filename = selectedFilenames[prefix]
    if (filename) {
      if (prefix === prefixes.hydraulics) {
        $.post(flameUrl('hydraulics'), {
          currentPlayback: filename
        })
      } else if (prefix === prefixes.poofer) {
        $.post(flameUrl('flame'), {
          currentPlayback: filename
        })
      }
    }
  }

  // Ajax callbacks
  var flameDataCallback = function(data) {
    updatePooferData(data)
    updateAllUIState()
  }
  var hydraulicsDataCallback = function(data) {
    updateHydraulicsData(data)
    updateAllUIState()
  }

  // Ajax promise factories
  var get = function(endpoint) {
    return $.get(flameUrl(endpoint))
  }
  var getFlameData = function() {
    return get('flame')
  }
  var getHydraulicsData = function() {
    return get('hydraulics')
  }

  // Setup polling
  var pollingFunction = function() {
    var polling = $('.polling-checkbox').is(':checked')
    if (!polling) return
    getFlameData().done(flameDataCallback)
    getHydraulicsData().done(hydraulicsDataCallback)
  }
  setInterval(pollingFunction, pollingInterval)

  // Make sure initial UI state is correct
  updateAllUIState()
})
