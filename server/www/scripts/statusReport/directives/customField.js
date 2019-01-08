// Faraday Penetration Test IDE
// Copyright (C) 2018  Infobyte LLC (http://www.infobytesec.com/)
// See the file 'doc/LICENSE' for the license information

angular.module('faradayApp')
    .directive('customField', [function () {
        return {
            restrict: 'E',
            scope: true,
            replace: true,
            template: '<div><div class="tab-pane-header">{{cf.field_display_name}}</div> \n\
                            <div class="form-group" ng-if="cf.field_type !== \'list\'"> \n\
                                <label class="sr-only" for="{{cf.field_name}}">{{cf.field_display_name}}</label> \n\
                                <input type="text" class="form-control input-sm" id="{{cf.field_name}}" name="{{cf.field_name}}" \n\
                                       placeholder="{{cf.field_display_name}}" \n\
                                       ng-model="modal.data.custom_fields[cf.field_display_name]" check-custom-type="{{cf.field_type}}" \n\
                                       uib-tooltip="{{(cf.field_type === \'int\') ? \'Type only numbers\' : \'Input type text\'}}"/> \n\
                            </div> \n\
                            <div class="form-group " ng-if="cf.field_type === \'list\'">\n\
                                <div class="input-group"> \n\
                                    <label class="sr-only" for="{{cf.field_name}}">{{cf.field_display_name}}</label> \n\
                                    <input type="text" class="form-control input-sm" id="{{cf.field_name}}" name="{{cf.field_name}}" \n\
                                           placeholder="{{cf.field_display_name}}" \n\
                                           ng-model="valueField" \n\
                                           uib-tooltip="Input type list"/> \n\
                                    <span class="input-group-addon cursor"><i class="fa fa-plus-circle" ng-click="newValueField(valueField)"></i></span> \n\
                                </div> \n\
                            </div> \n\
                            <div class="col-md-12 reference last-item-field" ng-repeat="item in modal.data.custom_fields[cf.field_display_name] track by $index" ng-class="{\'last-item-field\':$last}" ng-if="cf.field_type === \'list\'"> \n\
                                <div class="input-group margin-bottom-sm"> \n\
                                    <label class="sr-only" for="vuln-refs-create">{{cf.field_display_name}}</label> \n\
                                    <input type="text" class="form-control" id="vuln-refs-create" placeholder="{{cf.field_display_name}}" \n\
                                           ng-model="item.value" \n\
                                           role="button" readonly/> \n\
                                    <span class="input-group-addon cursor" ng-click="modal.data.custom_fields[cf.field_display_name].splice($index, 1)"> \n\
                                    <i class="fa fa-minus-circle"></i></span>                                \n\
                                    </div> \n\
                            </div> \n\
                        </div></div>',
            link: function (scope, element, attrs) {

                scope.newValueField = function (valueField) {
                    if (valueField !== "" && valueField !== undefined) {
                        if(scope.modal.data.custom_fields[scope.cf.field_display_name] == null )
                            scope.modal.data.custom_fields[scope.cf.field_display_name] = [];

                        // we need to check if the ref already exists
                        if (scope.modal.data.custom_fields[scope.cf.field_display_name].filter(function(field) {return field.value === valueField}).length === 0) {
                            scope.modal.data.custom_fields[scope.cf.field_display_name].push({value: valueField});
                            scope.valueField = "";
                        }
                        angular.element('#'+scope.cf.field_name).val("");
                    }
                }
            }
        }
    }]);
