import {React, Immutable, UrlParameters} from 'jimu-core';
import TestWidget from '../src/runtime/widget';
import {shallow, configure} from 'enzyme';
import {wrapWidget} from 'jimu-for-test';
import * as Adapter from 'enzyme-adapter-react-16';
configure({ adapter: new Adapter() });

jest.mock('../src/runtime/widget', () => {
  const Widget = (jest as any).requireActual('../src/runtime/widget');
  Widget.default.prototype.checkUrl = (url: string) => {}
  return Widget;
})

describe('iframe widget test', function() {

  describe('default config', function() {
    let config, Widget, wrapper;
    const manifest = { name: 'embed' } as any;
    beforeAll(function () {
      config = {
        embedType: 'url',
        staticUrl: 'https://www.arcgis.com/index.html'
      };
      Widget = wrapWidget(TestWidget, {
        config: config,
        manifest: manifest,
        queryObject: Immutable({} as UrlParameters)
      });
      wrapper = shallow(<Widget/>).shallow();
    });

    it('embed widget should be render', () => {
      expect(wrapper.find('.widget-embed').length).toEqual(1);
    });
  });
});
