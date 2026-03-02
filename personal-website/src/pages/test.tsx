import React from "react";
import cssInsertionModule0 from "./index.css.js";
import { makeStyles } from "@material-ui/styles";

const DEFAULT_BACKGROUND = "#F7931E";
const DEFAULT_TEXT_COLOR = "#FFFFFF";
const CLOUD_APP_ID = "612072808326-ws-custom-template";
const CLOUD_TK = "b7929fd1";

let tsdkPromise: Promise<any> | undefined;

function waitForCloud(timeout = 5000): Promise<any> {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const timer = setInterval(() => {
      const CloudCtor =
        (typeof window !== "undefined" && (window as any).Cloud) ||
        (typeof globalThis !== "undefined" && (globalThis as any).Cloud);
      if (CloudCtor) {
        clearInterval(timer);
        resolve(CloudCtor);
      } else if (Date.now() - start > timeout) {
        clearInterval(timer);
        reject(new Error("Cloud not injected"));
      }
    }, 100);
  });
}

const getTsdk = (): Promise<any> => {
  if (tsdkPromise) {
    return tsdkPromise;
  }

  tsdkPromise = (async () => {
    let CloudCtor =
      (typeof window !== "undefined" && (window as any).Cloud) ||
      (typeof globalThis !== "undefined" && (globalThis as any).Cloud);

    if (!CloudCtor) {
      try {
        CloudCtor = await waitForCloud(5000);
      } catch (e) {
        console.warn("tagsgroup 未找到 Cloud SDK：请确保已在页面引入 Cloud SDK 脚本或在微盟设计平台环境中运行", e);
        return null;
      }
    }

    try {
      return await CloudCtor.init({ tk: CLOUD_TK });
    } catch (error) {
      console.error("tagsgroup Cloud 初始化失败", error);
      tsdkPromise = undefined;
      throw error;
    }
  })();

  return tsdkPromise;
};
const wmrt = {
  rem: (rem) => {},
  style: (style) => {
    const styleObj = style.split(";").reduce((obj, pair) => {
      let [k, v] = pair.split(":");
      if (!k) return obj;
      k = k.trim();
      v = v.trim(); // style中 中划线转驼峰

      if (/-/.test(k)) {
        k = camelcase(k);
      }

      obj[k] = wmrt.rem(v);
      return obj;
    }, {});
    return styleObj;
  },
  cn: (className, componentName) => {
    if (className) {
      return className + "__" + componentName;
    }

    return className;
  },
  stringify: (value) => {
    if (value && typeof value === "object") {
      return JSON.stringify(value);
    }

    return value;
  },
  parse: (value) => {
    try {
      const v = JSON.parse(value);
      return v;
    } catch (e) {
      console.log(e);
      return value;
    }
  },
  detail: (event) => {
    event.detail = Object.assign({}, event.detail, event.target);
  },
  dataset: (event) => {
    datasetProxy(event.target);
    datasetProxy(event.currentTarget);
  },
};
const useStyles = makeStyles((theme) => {
  wmrt.rem = (value) => {
    if (/\d+(px|rpx)/.test(value)) {
      return value.replace(/(\d+)(px|rpx)/g, (_, number, unit) => {
        number = unit === "px" ? number * 2 : number;
        number = theme.rem(number);
        return number;
      });
    }

    return value;
  };

  return {
    root: {
      fontSize: theme.rem(24),
    },
  };
});

class BaseComponent extends React.PureComponent {
  setState(partialState, ...args) {
    // 最小变化原则
    const nextState = clonedeep(this.state);
    formatPartialState(partialState, nextState);
    super.setState(nextState, ...args);
  }

  componentWillMount() {
    this.data = new Proxy(this, {
      get(target, key) {
        if (target.props && target.props.hasOwnProperty(key)) {
          return target.props[key];
        } else if (target.state && target.state.hasOwnProperty(key)) {
          return target.state[key];
        } else {
          return target[key];
        }
      },
    });
  }

  util = {
    getValue: (state, prop) => {
      const layers = getLayers(prop);
      return getLayerValue(layers, state);
    },
    getLayers,
    isEqual,
  };
}

class Tagsgroup extends BaseComponent {
  state = {
    tags: [],
    styleInjections: [],
  };

  render() {
    console.log("开始render了");
    const displayTags = this.state.tags || [];

    return (
      <div className="custom-component-wrap__Tagsgroup">
        {this.state.styleInjections &&
          this.state.styleInjections.map((item, i) => (
            <style key={i}>{item}</style>
          ))}
        <div className="tagsgroup__Tagsgroup">
          <div className="tagsgroup__container__Tagsgroup">
            {displayTags.length ? (
              <React.Fragment>
                <div className="tagsgroup__list__Tagsgroup">
                  {displayTags.map((item, index) => (
                    <React.Fragment key={index}>
                      <div
                        className="tagsgroup__item__Tagsgroup"
                        style={{
                          backgroundColor: `${this.props.wmrt.rem(
                            item.backgroundColor
                          )}`,
                          color: `${this.props.wmrt.rem(item.textColor)}`,
                          borderColor: `${this.props.wmrt.rem(
                            item.backgroundColor
                          )}`,
                        }}
                      >
                        {item.text}
                      </div>
                    </React.Fragment>
                  ))}
                </div>
              </React.Fragment>
            ) : (
              <React.Fragment>
                {/* <span className="tagsgroup__empty__Tagsgroup">
                  请在扩展设置中添加标签
                </span> */}
              </React.Fragment>
            )}
          </div>
        </div>
      </div>
    );
  }

  constructor(props) {
    super(props);
    this.state.styleInjections = [];
  }

  updateTags = async (modelParam) => {
    let tsdk: any;

    try {
      tsdk = await getTsdk();
    } catch (error) {
      console.error("tagsgroup 获取 Cloud 实例失败", error);
    }

    if (!tsdk) {
      this.setState({ tags: [] });
      return;
    }

    let wid: string | undefined;

    try {
      if (typeof tsdk.getCurrentUserInfo === "function") {
        const res = await tsdk.getCurrentUserInfo();
        if (res && (res.code === 0 || res.code === "0")) {
          wid = res?.data?.wid;
          console.log("当前用户wid是", wid);
        }
      }
    } catch (error) {
      console.error("tagsgroup 获取用户信息失败", error);
    }

    if (!wid) {
      const model = modelParam || this.data.model || {};
      wid =
        model?.data?.styleSetting?.wid ||
        model?.data?.wid ||
        model?.styleSetting?.wid;

      if (!wid) {
        this.setState({ tags: [] });
        return;
      }
    }

    let response: any;

    try {
      if (typeof tsdk.request !== "function") {
        throw new Error("tsdk 缺少 request 方法");
      }

      response = await tsdk.request({
        url: "/tag/getTagByWid",
        data: { wid },
        requestOption: {
          header: {
            "cloud-app-id": CLOUD_APP_ID,
          },
        },
      });

      console.log("收到接口返回值", response);
    } catch (error) {
      console.error("tagsgroup 获取标签失败", error);
      this.setState({ tags: [] });
      return;
    }

    const list = (response && response.data) || [];

    if (!Array.isArray(list) || !list.length) {
      this.setState({ tags: [] });
      return;
    }

    const tags = list.reduce((result, item, index) => {
      if (!item) return result;
      const text =
        typeof item === "string" && item.trim()
          ? item.trim()
          : `标签 ${index + 1}`;
      result.push({
        text,
        backgroundColor: DEFAULT_BACKGROUND,
        textColor: DEFAULT_TEXT_COLOR,
      });
      return result;
    }, []);

    this.setState({ tags });
  };

  invokeObservers(prevProps = {}, prevState = {}) {
    if (prevProps === this.props && prevState === this.state) return;

    const invokeObserver = ([originalName, callback]) => {
      const valuesChanged = originalName
        .split(/\s*,\s*/)
        .reduce((total, name) => {
          let oldValue;
          let newValue;

          if (prevProps) {
            oldValue = this.util.getValue(prevProps, name);

            if (oldValue === undefined && prevState) {
              oldValue = this.util.getValue(prevState, name);
            }
          }

          newValue = this.util.getValue(this.props, name);

          if (newValue === undefined) {
            newValue = this.util.getValue(this.state, name);
          }

          if (!this.util.isEqual(newValue, oldValue)) {
            total.isChanged = true;
          }

          (total.res || (total.res = [])).push(newValue);
          return total;
        }, {});

      if (valuesChanged.isChanged) {
        callback.apply(this, valuesChanged.res);
      }
    };

    this.observers && Object.entries(this.observers).forEach(invokeObserver);
    this.properties &&
      Object.keys(this.properties).forEach((key) => {
        if (
          typeof this.properties[key].observer === "function" &&
          key.indexOf(".") === -1 &&
          key.indexOf("[") === -1
        ) {
          invokeObserver([key, this.properties[key].observer]);
        }
      });
  }

  componentDidMount() {
    this.invokeObservers();
    const cssModule0 = cssInsertionModule0;

    if (cssModule0) {
      this.setState(
        {
          styleInjections: this.state.styleInjections.concat(
            cssModule0(this.props.wmrt.rem)
          ),
        },
        () => {
          console.log("css modules 加载成功", this.state.styleInjections);
        }
      );
    }

    this.updateTags(this.data.model);
  }

  componentDidUpdate(prevProps, prevState) {
    this.invokeObservers(prevProps, prevState);
  }

  properties = {
    model: {
      type: Object,
      value: {},

      observer(newVal) {
        this.updateTags(newVal);
      },
    },
  };
}

export default (props) => {
  const classes = useStyles();
  return (
    <div className={classes.root}>
      <Tagsgroup {...props} wmrt={wmrt} />
    </div>
  );
};
/**
 * { 'obj.name': 'c', 'arr[0]': 0, 'obj.arr[2]': 2, 'obj.arr[2].name': 'lucy' }
 * { 'obj.arr3[1][1]': 'c' }
 */

function formatPartialState(partialState, nextState) {
  const props = Object.keys(partialState);
  const firstLayers = new Set();
  props.forEach((prop) => {
    formatProp(prop, partialState[prop], nextState, firstLayers);
  }); // 过滤掉没有修改的属性（只partialState的第一层）

  Object.keys(nextState).forEach((prop) => {
    !firstLayers.has(prop) && delete nextState[prop];
  });
}

function formatProp(prop, value, nextState, firstLayers) {
  const layers = getLayers(prop);
  setLayerValue(layers, nextState, value);
  firstLayers.add(layers[0].name);
}

function getLayers(prop) {
  return prop.split(".").reduce((pre, cur) => {
    // 嵌套数组
    if (/\[(\d+)\]/.test(cur)) {
      const arr = cur.split(/\[(\d+)\]/); // 嵌套多维数组

      const len = arr.length;

      if (len <= 3) {
        pre.push(
          {
            type: "array",
            name: arr[0],
          },
          {
            type: "object",
            name: arr[1],
          }
        );
      } else {
        pre.push({
          type: "array",
          name: arr[0],
        });

        for (let i = 1; i < len; i += 2) {
          pre.push({
            type: i + 2 < len ? "array" : "object",
            name: arr[i],
          });
        }
      }
    } else {
      pre.push({
        type: "object",
        name: cur,
      });
    }

    return pre;
  }, []);
}

function setLayerValue(layers, nextState, value) {
  layers.reduce((pre, cur, i, array) => {
    const { name, type } = cur; // 到数组最后一项赋值

    if (i === array.length - 1) {
      pre[name] = value;
      return pre;
    } // 处理新增的属性

    if (!pre[name]) {
      pre[name] = type === "array" ? [] : {};
    }

    return pre[name];
  }, nextState);
}

function getLayerValue(layers, state) {
  if (!state) return;
  const nextState = clonedeep(state);
  let value;
  layers.reduce((pre, cur, i, array) => {
    const { name, type } = cur; // 到数组最后一项赋值

    if (i === array.length - 1) {
      value = pre[name];
      return pre[name];
    } // 处理新增的属性

    if (!pre[name]) {
      pre[name] = type === "array" ? [] : {};
    }

    return pre[name];
  }, nextState);
  return value;
} // 简单实现，对于小程序的state的深拷贝场景足够使用

function clonedeep(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function isEqual(newValue, oldValue) {
  if (typeof newValue !== typeof oldValue) return false;

  if (Array.isArray(newValue) && Array.isArray(oldValue)) {
    return sameArray(newValue, oldValue);
  }

  if (
    newValue &&
    typeof newValue === "object" &&
    oldValue &&
    typeof oldValue === "object"
  ) {
    return sameObj(newValue, oldValue);
  }

  if (newValue !== oldValue) return false;
  return true;
} // false优先

function sameArray(arr1, arr2) {
  if (arr1.length !== arr2.length) return false;

  for (let i = 0; i < arr1.length; i++) {
    const v1 = arr1[i];
    const v2 = arr2[i];
    const res = isEqual(v1, v2);
    if (res) continue;
    else return false;
  }

  return true;
} // false优先

function sameObj(obj1, obj2) {
  if (typeof obj1 !== "object" || typeof obj2 !== "object") return false;
  const keys1 = obj1 ? Object.keys(obj1) : [];
  const keys2 = obj2 ? Object.keys(obj2) : [];
  if (keys1.length !== keys2.length) return false;

  for (let i = 0; i < keys1.length; i++) {
    const key = keys1[i];
    const v1 = obj1[key];
    const v2 = obj2[key];
    const res = isEqual(v1, v2);
    if (res) continue;
    else return false;
  }

  return true;
}

function datasetProxy(target) {
  if (target && !target.datasetDefined) {
    const dataset = target.dataset || {};
    const keys = Object.keys(dataset);
    const newDataset = {};
    keys.forEach((key) => {
      const value = dataset[key];
      newDataset[key] = wmrt.parse(value);
    });
    Object.defineProperty(target, "dataset", {
      get: function () {
        return newDataset;
      },
    });
    target.datasetDefined = true;
  }
}

function camelcase(name) {
  return name
    .split("-")
    .map((item, i) =>
      i === 0 ? item : item.charAt(0).toUpperCase() + item.slice(1)
    )
    .join("");
}
