<?php
/*
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
*/
namespace OPNsense\VLAN\Api;

use \OPNsense\Base\ApiMutableTableModelControllerBase;
use \OPNsense\VLAN\VLAN;
use \OPNsense\Core\Config;

class SettingsController extends ApiMutableTableModelControllerBase
{
    static protected $internalModelName = 'vlan';
    static protected $internalModelClass = '\OPNsense\VLAN\VLAN';
    static protected $gridFields = array('ParentInterface', 'VLANTag', 'Description');

    // FIXME Code to check for duplicate VLANs. This should actually be in the
    // model, ideally, not in the API controller.

    private function duplicateVLANCheck($newnode)
    {
        $newnodeA = $newnode->getAttributes();
        $parentInterface = (string)$newnode->ParentInterface;
        $vlanTag = (string)$newnode->VLANTag;
        if (array_key_exists("uuid", $newnode->getAttributes())) {
            $skipUUID = $newnodeA["uuid"];
        } else {
            $skipUUID = null;
        }
        foreach ($this->getNodes()->sortedBy(array(), false) as $node) {
            $nodeA = $node->getAttributes();
            if ($nodeA['uuid'] == $skipUUID) {
                continue; // don't compare with self
            }
            if ((string)$node->ParentInterface != $parentInterface) {
                continue;
            }
            if ((string)$node->VLANTag != $vlanTag) {
                continue;
            }
            return "Cannot set duplicate VLANs.";
        }
    }

    protected function setItemActionHook($newnode)
    {
        return $this->duplicateVLANCheck($newnode);
    }

    protected function addItemActionHook($newnode)
    {
        return $this->duplicateVLANCheck($newnode);
    }
}
