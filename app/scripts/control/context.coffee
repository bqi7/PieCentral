angular.module('daemon.context', [])

.controller('CanvasContextCtrl', [
  '$scope'
  ($scope) ->

    $scope.menuItems = [
      class: 'dropdown-header'
      label: 'Visualize'
    ,
      label: 'Mock Peripheral'
      ngClick: $scope.addWidget
    ,
      class: 'divider'
    ,
      label: 'Close All Widgets'
      ngClick: $scope.removeAllWidgets
    ]
  ])

.directive('canvascontext', [
  ->
    return {
      restrict: 'E'
      templateUrl: '/partials/canvascontext.html'
      link: (scope, elem, attrs) ->
        $('#widget-container').contextmenu({
          before: (e, element, target) ->
            if $(e.target).is('#widget-container')
              return true
            return false
        })
    }
  ])

.directive('widgetcontext', [
  ->
    return {
      restrict: 'E'
      templateUrl: '/partials/widgetcontext.html'
    }
  ])

.directive('widgetcontextcaller', [
  ->
    return {
      restrict: 'A'
      link: (scope, elem, attrs) ->
        target = '#widget-context-menu'
        $(elem[0]).contextmenu(
            target: target
            before: (e, context) ->
              scope.setRecentWidget(scope.widget)
            onItem: (context, e) ->
              this.closemenu()
              scope.removeRecentWidget()
          )
    }
  ])