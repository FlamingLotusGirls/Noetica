$(function ($) {
  // Constants
  var flameHost = 'noetica-flames.local:5000'
  var pollingInterval = 1000 // in milliseconds
  var prefixes = {
    hydraulics: 'hydraulics-attract',
    poofer: 'poofer-sequence'
  }

  // Initial values
  var selectedPoofer = null
  var inverted = false
  var selectedFilenames = {}
  var toggleStates = {
    'poofer-main': true,
    'hydraulics-main': true,
    'hydraulics-attract': true
  }
  var hydraulicsAttractModeActive = false
  var pooferSequenceModeActive = false
  var hydraulicsRecordActive = false
  var hydraulicsState = {control_x:0,control_y:0,control_z:0,sculpture_x:0,sculpture_y:0,sculpture_z:0}
  var hydraulicsAttractFiles = []
  var pooferSequenceFiles = []

  // jQuery helpers
  $.fn.reduce = function() {
    return [].reduce.apply(this.toArray(), arguments)
  }

  // Helper functions
  var flameUrl = function(endpoint) {
    if (endpoint === undefined) {
      endpoint = ''
    }
    return `http://${flameHost}/flame${endpoint}`
  }
  var hydraulicsUrl = function(endpoint) {
    if (endpoint === undefined) {
      endpoint = ''
    }
    return `http://${flameHost}/hydraulics${endpoint}`
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
  var updateToggleState = function(prefix) {
    var $element = $(`.${prefix}-toggle-button`)
    var state = toggleStates[prefix]
    $element.prop('checked', state)
  }
  var updateToggleStates = function() {
    Object.keys(toggleStates).map(updateToggleState)
  }
  var updatePooferToggleButtonState = function() {
    var enabled = !selectedPoofer || selectedPoofer.enabled
    $('.poofer-individual-toggle-button').prop('checked', enabled)
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
      $poofer.removeClass('poofer-disabled')
      $poofer.addClass('poofer-enabled')
    } else {
      $poofer.removeClass('poofer-enabled')
      $poofer.addClass('poofer-disabled')
    }
  }
  var updateAllPoofersDisplayState = function() {
    allPoofers.forEach(function (pooferName) {
      var poofer = allPoofersState[pooferName]
      updatePooferDisplayState(poofer)
    })
  }
  var updateHydraulicsDisplayState = function() {
    ['control_x','control_y','control_z','sculpture_x','sculpture_y','sculpture_z'].forEach(function(coord) {
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
      $file.remove()
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
    var oldMode = hydraulicsAttractModeActive
    var $button = $('.hydraulics-attract-play-stop-button')
    if (!selectedHydraulicsFilename()) {
      hydraulicsAttractModeActive = false
      $button.attr('disabled', true)
    } else if (!toggleStates['hydraulics-attract']) {
      $button.attr('disabled', true)
    } else {
      $button.attr('disabled', false)
    }
    if (hydraulicsAttractModeActive) {
      $button.removeClass('btn-play')
      $button.addClass('btn-stop')
    } else {
      $button.removeClass('btn-stop')
      $button.addClass('btn-play')
    }
    $button.attr('title', hydraulicsAttractModeActive ? 'Stop' : 'Start')
    if (hydraulicsAttractModeActive !== oldMode) {
      postHydraulicsAttractMode()
    }
  }
  var updatePooferSequencePlayMode = function() {
    var oldMode = pooferSequenceModeActive
    var $button = $('.poofer-sequence-play-stop-button')
    if (!selectedPooferFilename()) {
      pooferSequenceModeActive = false
      $button.attr('disabled', true)
    } else {
      $button.attr('disabled', false)
    }
    if (pooferSequenceModeActive) {
      $button.removeClass('btn-play')
      $button.addClass('btn-stop')
    } else {
      $button.removeClass('btn-stop')
      $button.addClass('btn-play')
    }
    $button.attr('title', pooferSequenceModeActive ? 'Stop' : 'Start')
    if (pooferSequenceModeActive !== oldMode) {
      postPooferSequenceMode()
    }
  }
  var updateHydraulicsRecordButtonState = function() {
    var $button = $('.hydraulics-record-toggle-button')
    if (hydraulicsRecordActive) {
      $button.removeClass('btn-record')
      $button.addClass('btn-stop-record')
    } else {
      $button.removeClass('btn-stop-record')
      $button.addClass('btn-record')
    }
    $button.attr('title', hydraulicsAttractModeActive ? 'Stop Recording' : 'Record')

  }
  var updateSelectedFileDependentState = function() {
    updateHydraulicsAttractPlayMode()
    updatePooferSequencePlayMode()
  }
  var updateColorInversion = function() {
    if (inverted) {
      $('html').addClass('inverted')
    }
    else {
      $('html').removeClass('inverted')
    }
  }
  var updateAllUIState = function() {
    // Since we don't have automatic data binding and it's a pain to call update functions
    // in just the right places, this function just updates everything and is called
    // when anything changes. Where possible, functions called from here should be
    // written to not force refreshes of state that didn't actually change.
    updateToggleStates()
    updateSelectedPooferDependentState()
    updateAllPoofersDisplayState()
    updateHydraulicsDisplayState()
    updateHydraulicsAttractFilePicker()
    updatePooferSequenceFilePicker()
    updateSelectedFileDependentState()
    updateHydraulicsRecordButtonState()
    updateColorInversion()
  }

  // Data state setting functions
  var setSelectedPoofer = function(name) {
    selectedPoofer = allPoofersState[name]
    updateSelectedPooferDependentState()
  }
  var updatePooferData = function (data) {
    toggleStates['poofer-main'] = data.globalState
    data.poofers.forEach(function(poofer) {
      var pooferState = allPoofersState[poofer.id.toLowerCase()]
      pooferState.enabled = poofer.enabled
    })
    pooferSequenceFiles = data.patterns.map(function(p) { return p.name })
  }
  var updateHydraulicsData = function (data) {
    toggleStates['hydraulics-main'] = data.currentState === 'nomove' ? false : true
    toggleStates['hydraulics-attract'] = data.autoAttractEnabled
    hydraulicsAttractModeActive = data.currentState === 'attract' ? true : false
    hydraulicsState = data
    hydraulicsAttractFiles = data.playbacks
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
    inverted = !inverted
    updateAllUIState()
  })
  $('.poofer-individual-toggle-button').on('click', function () {
    if (selectedPoofer) {
      selectedPoofer.enabled = !selectedPoofer.enabled
      updatePooferDisplayState(selectedPoofer)
      updatePooferToggleButtonState()
      var name = selectedPoofer.name.toUpperCase()
      $.post(flameUrl(`/poofers/${name}`), { enabled: selectedPoofer.enabled })
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
    hydraulicsAttractModeActive = !hydraulicsAttractModeActive
    postHydraulicsAttractPlayStop()
    updateAllUIState()
  })
  $('.poofer-sequence-play-stop-button').on('click', function() {
    pooferSequenceModeActive = !pooferSequenceModeActive
    postPooferSequenceMode()
    updateAllUIState()
  })
  $('.hydraulics-record-toggle-button').on('click', function() {
    hydraulicsRecordActive = !hydraulicsRecordActive
    postHydraulicsRecordMode()
    updateAllUIState()
  })
  Object.keys(toggleStates).forEach(function(p) {
    var prefix = p
    $(`.${prefix}-toggle-button`).on('click', function() {
      toggleStates[prefix] = !toggleStates[prefix]
      postToggleState(prefix)
      updateAllUIState()
    })
  })
  $('.hydraulics-attract-rename-button').on('click', function () {
    postHydraulicsAttractRename()
  })
  $('.hydraulics-attract-trash-button').on('click', function () {
    deleteHydraulicsAttractFile()
  })

  // Ajax functions
  var postHydraulicsAttractMode = function() {
    if (hydraulicsAttractModeActive && selectedHydraulicsFilename()) {
      $.post(hydraulicsUrl(), {
        state: 'attract',
        currentPlayback: selectedHydraulicsFilename()
      })
    } else {
      // just in case, make state consistent
      hydraulicsAttractModeActive = false
      $.post(hydraulicsUrl(), {
        state: 'passthrough'
      })
    }
  }
  var postPooferSequenceMode = function() {
    var name = selectedPooferFilename()
    if (name) {
      $.post(flameUrl(`/patterns/${name}`), {
        active: pooferSequenceModeActive
      })
    } else {
      // just in case, make state consistent
      pooferSequenceModeActive = false
    }
  }
  postHydraulicsRecordMode = function() {
    $.post(hydraulicsUrl('/playbacks'), {
      record: '' + hydraulicsRecordActive
    })
  }
  var postHydraulicsAttractRename = function() {
    var oldName = selectedHydraulicsFilename()
    var newName = $('.hydraulics-attract-name-field').val()
    if (!oldName || !newName) {
      return
    }
    $.post(hydraulicsUrl(`/playbacks/${oldName}`), {
      newName: newName
    })
  }
  var deleteHydraulicsAttractFile = function() {
    var filename = selectedHydraulicsFilename()
    if (!filename) {
      return
    }
    $.ajax(hydraulicsUrl(`/playbacks/${filename}`), {
      method: 'DELETE'
    })
  }
  var postAttractFile = function(prefix) {
    var filename = selectedFilenames[prefix]
    if (filename) {
      if (prefix === prefixes.hydraulics) {
        $.post(hydraulicsUrl(), {
          currentPlayback: filename
        })
      } else if (prefix === prefixes.poofer) {
        // Do nothing - poofer filenames work differently
      }
    }
  }
  var postToggleState = function(prefix) {
    if (prefix === 'poofer-main') {
      $.post(flameUrl(), {
        playState: toggleStates[prefix] ? 'play' : 'pause'
      })
    } else if (prefix === 'hydraulics-main') {
      $.post(hydraulicsUrl(), {
        state: toggleStates[prefix] ? 'passthrough' : 'nomove'
      })
    } else if (prefix === 'hydraulics-attract') {
      if (toggleStates['hydraulics-main']) {
        $.post(hydraulicsUrl(), {
          autoAttractEnabled: toggleStates[prefix]
        })
      }
    }
  }
  var postHydraulicsAttractPlayStop = function() {
    $.post(hydraulicsUrl(), {
      state: hydraulicsAttractModeActive ? 'attract' : 'passthrough'
    })
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

  // Setup polling
  var pollingFunction = function() {
    $.getJSON(flameUrl()).done(flameDataCallback)
    $.getJSON(hydraulicsUrl()).done(hydraulicsDataCallback)
  }
  setInterval(pollingFunction, pollingInterval)

  // Make sure initial UI state is correct
  updateAllUIState()
})
