{#
Copyright (c) 2016, IT-assistans Sverige AB
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
#}

<script type="text/javascript">

    $( document ).ready(function() {

        /*************************************************************************************************************
         * link grid actions
         *************************************************************************************************************/

        $("#grid-vlans").UIBootgrid(
            {   search:'/api/vlan/settings/searchItems',
                get:'/api/vlan/settings/getItem/',
                set:'/api/vlan/settings/setItem/',
                add:'/api/vlan/settings/addItem/',
                del:'/api/vlan/settings/delItem/',
                toggle:'/api/vlan/settings/toggleItem/'
            }
        );
    });

</script>

<div id="vlans" class="tab-pane fade in active">
    <!-- tab page "vlans" -->
    <table id="grid-vlans" class="table table-condensed table-hover table-striped table-responsive" data-editDialog="EditVLAN">
        <thead>
        <tr>
            <th data-column-id="origin" data-type="string" data-visible="false">{{ lang._('Origin') }}</th>
            <th data-column-id="enabled" data-width="6em" data-type="string" data-formatter="rowtoggle">{{ lang._('Enabled') }}</th>
            <th data-column-id="number" data-type="number"  data-visible="false">{{ lang._('Number') }}</th>
            <th data-column-id="bandwidth" data-type="number">{{ lang._('Bandwidth') }}</th>
            <th data-column-id="bandwidthMetric" data-type="string">{{ lang._('Metric') }}</th>
            <!--<th data-column-id="burst" data-type="number">{{ lang._('Burst') }}</th>--> <!-- disabled, burst does not work -->
            <th data-column-id="mask" data-type="string">{{ lang._('Mask') }}</th>
            <th data-column-id="description" data-type="string">{{ lang._('Description') }}</th>
            <th data-column-id="commands" data-width="7em" data-formatter="commands" data-sortable="false">{{ lang._('Commands') }}</th>
            <th data-column-id="uuid" data-type="string" data-identifier="true"  data-visible="false">{{ lang._('ID') }}</th>
        </tr>
        </thead>
        <tbody>
        </tbody>
        <tfoot>
        <tr>
            <td></td>
            <td>
                <button data-action="add" type="button" class="btn btn-xs btn-default"><span class="fa fa-plus"></span></button>
                <button data-action="deleteSelected" type="button" class="btn btn-xs btn-default"><span class="fa fa-trash-o"></span></button>
            </td>
        </tr>
        </tfoot>
    </table>
</div>

<div class="col-md-12">
    <hr/>
    <button class="btn btn-primary"  id="reconfigureAct" type="button"><b>{{ lang._('Apply') }}</b><i id="reconfigureAct_progress" class=""></i></button>
    <br/><br/>
</div>

{# include dialogs #}
{{ partial("layout_partials/base_dialog",['fields':formEdit,'id':'EditVLAN','label':'Edit VLAN'])}}
